from faker import Faker
from helper import register_encounter
import random

fake = Faker()

evidence = "https://pixelfed.pastabytes.com/storage/m/_v2/788885648660197377/634f2a4e4-291f24/U1YsUt7JD000/AbjjjAQj2fFcYf90HOGZajoUNdhHRSpJ7L2y4hEV_thumb.jpg"

species = []

with open("resources/bird_species.txt", "r") as f:
    species = [line.rstrip() for line in f.readlines()]

for _ in range(100):
    bird = random.choice(species)
    time = random.randint(1738353419-(3600*168*54*5), 1738353419)
    user = f"https://pixelfed.pastabytes.com/{fake.last_name().lower()}.{fake.first_name().lower()}"
    latlng = fake.local_latlng(coords_only = True)

    register_encounter(time=time, user=user, evidence=evidence, species=bird, latitude=latlng[0], longitude=latlng[1])
