import time
from docling.document_converter import DocumentConverter
import os
import json

def docling_test(source, filename, destination_folder):
    os.makedirs(destination_folder, exist_ok=True)
    print(f"Converting {filename} to markdown, html, and json...")

    if(os.path.exists(f"{destination_folder}/{filename}.md") and
       os.path.exists(f"{destination_folder}/{filename}.html") and
       os.path.exists(f"{destination_folder}/{filename}.json")):
        print(f"Skipping conversion for {filename}, output files already exist.")
        return

    start_time = time.time()

    #converter = DocumentConverter(source=source, target="json", output_dir="C:/Users/Zaphare/OneDrive - FHNW/0_MSC/0_Thesis/Research_Papers/KGG")
    converter = DocumentConverter()

    result = converter.convert(source)
    markdown_result = result.document.export_to_markdown()
    html_result = result.document.export_to_html()
    dict_result = result.document.export_to_dict()

    end_time = time.time()
    diff_time = end_time - start_time
    print(f"Document conversion for {filename} took {diff_time:.2f} seconds")

    # store to files
    with open(f"{destination_folder}/{filename}.md", "w", encoding="utf-8") as f:
        f.write(markdown_result)

    with open(f"{destination_folder}/{filename}.html", "w", encoding="utf-8") as f:
        f.write(html_result)

    with open(f"{destination_folder}/{filename}.json", "w", encoding="utf-8") as f:
        json.dump(dict_result, f, ensure_ascii=False, indent=4)

    return diff_time

if __name__ == "__main__":
    # docling_test("C:/Users/Zaphare/OneDrive - FHNW/0_MSC/0_Thesis/Research_Papers/KGG/KGG_3.pdf", "KGG_7", "C:/Users/Zaphare/OneDrive - FHNW/0_MSC/0_Thesis/Research_Papers/KGG/conversion")

    time_tracker = {}

    # scan os folder and convert all pdf files
    folder_path_pc = "C:/Users/Zaphare/OneDrive - FHNW/0_MSC/0_Thesis/Research_Papers/KGG/"
    folder_path = "C:/Users/lukas/OneDrive - FHNW/0_MSC/0_Thesis/Research_Papers/KGG/"

    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            time_spent = docling_test(os.path.join(folder_path, filename), filename.replace(".pdf", ""), "C:/Users/lukas/OneDrive - FHNW/0_MSC/0_Thesis/Research_Papers/KGG/conversion")
            time_tracker[filename] = time_spent

    # Print the time taken for each file
    for pdf_file, time_taken in time_tracker.items():
        print(f"Time taken for {pdf_file}: {time_taken:.2f} seconds")