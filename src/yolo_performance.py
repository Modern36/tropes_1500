from ml_data.files import get_raw_gender_df

from paths_20 import data_file, read_data


def has_person(row):
    return any(row[["child", "gender: other", "man", "woman"]])


def add_gtp():
    original_data = read_data()

    original_data.sort_values(by="id", inplace=True)

    if "gtp" in original_data.columns:
        print("person ground truth already in data")
    else:
        print("adding person ground truth to data...")
        raw_classification = get_raw_gender_df()

        raw_classification.sort_values(by="id", inplace=True)

        if all(raw_classification.id != original_data.id):
            raise ValueError("ids don't match")

        original_data["gt_p"] = raw_classification.apply(has_person, axis=1)

        original_data.to_csv(data_file, index=False)
    return original_data


if __name__ == "__main__":
    add_gtp()
