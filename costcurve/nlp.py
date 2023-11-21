from time import sleep
from logging import getLogger
import requests
from typing import List
from tqdm import tqdm
logger = getLogger(__name__)
def get_huggingface_api_key(path: str = "huggingface_key.txt") -> str:
    with open(path, "r") as f:
        key = f.read()
    return key

def retry(request_fun):

    def wrapper(*args, **kwargs):
        response = request_fun(*args, **kwargs)
        if "error" in response:
          if "estimated_time" in response:
            wait_time = round(response["estimated_time"]) + 1
            logger.info(f"Waiting {wait_time}s for model to load")
            sleep(wait_time)
            response = request_fun(*args, **kwargs)
          else:
              raise RuntimeError(f"An error occured: {response}")
        return response

    return wrapper

def isit(x: str, y: str) -> float:
    """Query NLI model to ask if x is a kind of y.

    """

    API_URL = "https://api-inference.huggingface.co/models/roberta-large-mnli"
    headers = {"Authorization": f"Bearer {get_huggingface_api_key()}"}
    payload = {
	"inputs": f" x is a {x} Therefore x is a {y}.",
}
    response = requests.post(API_URL, headers=headers, json=payload).json()[0]
    entailment_score = None
    for label in response:
        if label["label"] == "ENTAILMENT":
            entailment_score = label["score"]
    #FIXME change this to a boolean
    return entailment_score

@retry
def get_food_entities(inputs):
    #TODO we might be able to batch several of these line items into a single request somehow
    #if rate limiting/cost becomes an issue

    #distillbert seems to behave *very* differently with all caps.
    line_item = inputs.lower()
    API_URL = "https://api-inference.huggingface.co/models/chambliss/distilbert-for-food-extraction"
    headers = {"Authorization": f"Bearer {get_huggingface_api_key()}"}
    payload = {
	"inputs": line_item,
}
    response = requests.post(API_URL, headers=headers, json=payload).json()
    return response


def parse_line_items(line_items: List[str]) -> List[str]:
    """
    Extract the food entities from each line item

    Example:


    line_items = ["FRESH SQUID 5-8 R&T (LOLIGO) 1/10# (TUBS) WILD-USA (PRICED BY THE TUB)",
              "BLACK GROUPER FILLET, SKIN OFF, GULF OG MEXICO, PC RF 40",
              "FRESH SALMON FILLET, CFW, SKIN ON, FARM, SCOTLAND 10",
              "FRESH SEA SCALLOPS, U/10 CT. DRY (SEA TRADE) 1 GAL. WILD, USA",
              "FRESH MUSSELS, BLK. 1/10# FARM, PRINCE EDWARD, ISLAND",
              "9-11oz. FRESH WHITE TROUT FILLETS B-FLY FARM, COLOMBIA",
              "Pasteruized Lump Blue Crab Meat (Pelagicus)-Packer 12/1# Wild-Indonesia",
              "16/20 P&D Tail-on Raw White Shrimp-Packer 5/2# Farm",
              "6oz. Mahi Portions (IVP)-Packer1/10# Wild-Peru/Vietnam",
              "SHIPPING AND HANDING"]

    >> parse_line_items(line_items)

    >> ['squid loligo tub',
     '##er fillet skin g mexico',
     'salmon fillet cw skin scotland',
     'sea scallops',
     'mussels',
     'white trout fillets b - fly colo',
     'lump blue crab meat pelagicus',
     'white shrimp pack',
     'mahi portions']
              """


    def parse_line_item(line_item: str):
        food_entities = get_food_entities(line_item)
        food_entities = [e["word"] for e in food_entities if e["entity_group"] in ["LABEL_0", "LABEL_1"]]
        return food_entities

    def parse_lst(lst: List[str]):
        s = lst[0]
        for it in lst[1:]:
            if it.startswith("##"):
                s += it.lstrip("##")
            else:
                s += f" {it}"
        return s

    parsed_items = [parse_line_item(li) for li in tqdm(line_items,"line item")]
    parsed_lists = [parse_lst(lst) for lst in parsed_items if lst]
    return parsed_lists