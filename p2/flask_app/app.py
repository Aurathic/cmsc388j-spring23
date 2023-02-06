from flask import Flask, render_template
from model import PokeClient

app = Flask(__name__)

poke_client = PokeClient()


@app.route("/")
def index():
    """
    Must show all of the pokemon names as clickable links

    Check the README for more detail.
    """
    pokemon_list = poke_client.get_pokemon_list()
    return render_template("index.html", pokemon_list=pokemon_list)


@app.route("/pokemon/<pokemon_name>")
def pokemon_info(pokemon_name):
    """
    Must show all the info for a pokemon identified by name

    Check the README for more detail
    """
    pokemon_info = poke_client.get_pokemon_info(pokemon_name)
    return render_template(
        "pokemon.html",
        name=pokemon_info["name"],
        height=pokemon_info["height"],
        weight=pokemon_info["weight"],
        base_exp=pokemon_info["base_exp"],
        moves=pokemon_info["moves"],
        abilities=pokemon_info["abilities"],
    )


@app.route("/ability/<ability_name>")
def pokemon_with_ability(ability_name):
    """
    Must show a list of pokemon

    Check the README for more detail
    """

    pokemon_with_ability_list = poke_client.get_pokemon_with_ability(ability_name)
    return render_template(
        "ability.html",
        ability_name=ability_name,
        pokemon_with_ability=pokemon_with_ability_list,
    )
