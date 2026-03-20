#!/usr/bin/env python3
"""
LoRA Fine-Tuning on Finance Data
Run: python finance_lora.py
"""

from __future__ import annotations

import os

import torch
from datasets import Dataset
from peft import LoraConfig, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)

from finance_config import (
    ADAPTERS_DIR,
    CORPUS_LIMIT,
    GENERATION_MODEL_NAME,
    MAX_LENGTH,
    OUTPUT_DIR,
    TEST_PROMPTS,
)
from finance_knowledge import build_training_texts


os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


def build_dataset(limit: int = CORPUS_LIMIT) -> Dataset:
    return Dataset.from_dict({"text": build_training_texts(limit=limit)})


def load_tokenizer(model_name: str = GENERATION_MODEL_NAME) -> AutoTokenizer:
    tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
    tokenizer.pad_token = tokenizer.eos_token
    return tokenizer


def tokenize_dataset(dataset: Dataset, tokenizer: AutoTokenizer, max_length: int = MAX_LENGTH) -> Dataset:
    def tokenize_function(examples):
        tokenized = tokenizer(
            examples["text"],
            padding="max_length",
            truncation=True,
            max_length=max_length,
        )
        tokenized["labels"] = tokenized["input_ids"].copy()
        return tokenized

    return dataset.map(tokenize_function, batched=True, remove_columns=["text"])


def create_lora_model(model_name: str = GENERATION_MODEL_NAME):
    base_model = AutoModelForCausalLM.from_pretrained(model_name, local_files_only=True)
    lora_config = LoraConfig(
        r=8,
        lora_alpha=32,
        target_modules=["c_attn"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    return get_peft_model(base_model, lora_config)


def create_trainer(model, tokenized_dataset: Dataset, tokenizer: AutoTokenizer) -> Trainer:
    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        num_train_epochs=3,
        per_device_train_batch_size=2,
        save_steps=10,
        logging_steps=2,
        report_to="none",
    )
    return Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
    )


def generate_answer(model, tokenizer: AutoTokenizer, prompt: str, device: torch.device) -> str:
    templated = f"Question: {prompt}\nAnswer:"
    inputs = tokenizer(templated, return_tensors="pt", padding=True, truncation=True)
    inputs = {key: value.to(device) for key, value in inputs.items()}

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=48,
            temperature=0.3,
            do_sample=True,
            top_p=0.8,
            num_beams=4,
            no_repeat_ngram_size=3,
            repetition_penalty=1.2,
            early_stopping=True,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id,
        )

    decoded = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    answer = decoded.split("Answer:", 1)[-1].strip()
    return " ".join(answer.split())


def main() -> None:
    print("\n1. Preparing finance training data...")
    dataset = build_dataset(limit=CORPUS_LIMIT)
    print(f"   \u2713 Created {len(dataset)} QA-style training examples")

    print("\n2. Tokenizing data...")
    tokenizer = load_tokenizer()
    tokenized_dataset = tokenize_dataset(dataset, tokenizer)
    print("   \u2713 Tokenized")

    print("\n3. Loading base model...")
    model = create_lora_model()
    trainable_params = sum(param.numel() for param in model.parameters() if param.requires_grad)
    total_params = sum(param.numel() for param in model.parameters())
    print(f"   \u2713 Loaded {GENERATION_MODEL_NAME}")
    print(f"   \u2713 Trainable: {trainable_params:,} / {total_params:,} ({100 * trainable_params / total_params:.2f}%)")

    print("\n4. Training...")
    trainer = create_trainer(model, tokenized_dataset, tokenizer)
    trainer.train()
    print("   \u2713 Training complete")

    print("\n5. Saving adapters...")
    model.save_pretrained(str(ADAPTERS_DIR))
    print(f"   \u2713 Saved to {ADAPTERS_DIR}")

    print("\n6. Testing fine-tuned model...")
    model.eval()
    device = torch.device("cpu")
    model.to(device)
    for prompt in TEST_PROMPTS:
        response = generate_answer(model, tokenizer, prompt, device)
        print(f"\n   Q: {prompt}")
        print(f"   A: {response}")


if __name__ == "__main__":
    main()
