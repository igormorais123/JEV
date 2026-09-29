"""Synthetic, public fixture. Expected: normalize=True, add=False for strip question."""


def normalize(value):
    return value.strip()


def add(left, right):
    return left + right
