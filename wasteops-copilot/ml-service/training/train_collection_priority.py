"""Validate and serialize the transparent priority scorer."""

from app.models.collection_priority_model import CollectionPriorityModel


def train():
    return CollectionPriorityModel()
