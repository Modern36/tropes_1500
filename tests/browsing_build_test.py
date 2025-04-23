from trope_paths import raw_dir, resolve_image_path

filenames = [p.with_suffix("").name for p in raw_dir.iterdir()]


def resolve_model_paths(model):
    for name in filenames:
        file_path = resolve_image_path(name, model)
        assert file_path.exists()


def test_DinoManWoman_mapping():
    resolve_model_paths("DinoManWoman")


def test_DinoWomanMan_mapping():
    resolve_model_paths("DinoWomanMan")


def test_YOLO_90_mapping():
    resolve_model_paths("YOLO_90")


def test_YOLO_75_mapping():
    resolve_model_paths("YOLO_75")


def test_YOLO_50_mapping():
    resolve_model_paths("YOLO_50")
