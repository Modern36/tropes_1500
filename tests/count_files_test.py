import pytest

from trope_paths import model_output

subdirs = list(model_output.iterdir())


def test_count_DinoManWoman_th25():
    assert 1500 == len(list((model_output / "DinoManWoman_th25").iterdir()))


def test_count_DinoWoman_th25():
    assert 1500 == len(list((model_output / "DinoWoman_th25").iterdir()))


def test_count_ollama_description_output():
    assert 1500 == len(
        list((model_output / "ollama_description_output").iterdir())
    )


def test_count_yolos_pretrained_th75():
    assert 1500 == len(
        list((model_output / "yolos-pretrained_th75").iterdir())
    )


def test_count_DinoM_n_th25():
    assert 1500 == len(list((model_output / "DinoMan_th25").iterdir()))


def test_count_yolos_pretrained_th50():
    assert 1500 == len(
        list((model_output / "yolos-pretrained_th50").iterdir())
    )


def test_count_yolos_pretrained_th90():
    assert 1500 == len(
        list((model_output / "yolos-pretrained_th90").iterdir())
    )


def test_count_DinoWomanMan_th25():
    assert 1500 == len(list((model_output / "DinoWomanMan_th25").iterdir()))
