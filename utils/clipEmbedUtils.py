import torch
import open_clip
import faiss
import numpy as np

import globals

from PIL import Image
from io import BytesIO
from logging import getLogger

model = None
preprocess = None
device = "cpu"

logger = getLogger("ClankerMod")

def initClip():
    global model
    global preprocess
    global device
    #CPU Mode or GPU but fall back to CPU if GPU not available.
    match(globals.configDict["ClipProcessor"]):
        case "cpu":
            device = "cpu"
        case _:
            device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"CLIP + FAISS device: {device}")

    model, preprocess, _ = open_clip.create_model_and_transforms(
        "ViT-B-32",
        pretrained="openai"
    )
    model = model.to(device)
    model.eval()

    #dim = 512
    #index = faiss.IndexFlatIP(dim)

@torch.no_grad()
def getEmbedding(imageBytes):
    image = Image.open(BytesIO(imageBytes)).convert("RGB")
    image = preprocess(image).unsqueeze(0).to(device)
    emb = model.encode_image(image)
    emb = emb / emb.norm(dim=-1, keepdim=True)
    return emb.cpu().numpy().astype("float32")[0]