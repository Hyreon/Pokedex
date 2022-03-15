#ONLY GENERATION 4 GAMES HAVE DATA.
#IF NO DATA, NO ATTEMPT IS MADE AT UPLOADING.
#SOME DATA IS HARD-CODED RATHER THAN FROM FILES.
#ADDING OTHER GAMES TO TRADE WITH IS NOT YET IMPLEMENTED.
#COULD ADD A SUMMARY, INDICATING HOW MANY POKES CAN BE CAUGHT, AND HOW DIFFICULT THEY ARE.

import requests
import io
import re
import json

#enums - high is harder
NONEXISTANT = 6 #no game data for the pokemon exists for this game, eg future generations, melmetal in s/m
IMPOSSIBLE = 5 #this pokemon was never obtainable in this game
MYTHICAL = 4 #this pokemon requires spin-off games or timed events to obtain
EXOTIC = 3.2 #only sometimes available in a game
EPIC = 3 #limited amount (no breeding, or breeding is irrelevant bc item is the bottleneck)
RARE = 2 #exceptionally difficult to obtain
UNCOMMON = 1 #low catch rate, limited time, or extra effort required to obtain
COMMON = 0 #very few extra steps to obtain

def rarity_value(string):
    if string == "NONEXISTANT":
        return NONEXISTANT
    elif string == "IMPOSSIBLE":
        return IMPOSSIBLE
    elif string == "MYTHICAL":
        return MYTHICAL
    elif string == "EXOTIC":
        return EXOTIC
    elif string == "EPIC":
        return EPIC
    elif string == "RARE":
        return RARE
    elif string == "UNCOMMON":
        return UNCOMMON
    elif string == "COMMON":
        return COMMON

friendly_names = {}
species_names = {}
species_egg_group = {}

forbidden_conditions = ['slot2-ruby', 'slot2-sapphire', 'slot2-emerald', 'slot2-firered', 'slot2-leafgreen']    #conditions that are impossible without another cartridge
forbidden_evolution_triggers = ['trade']    #evolution triggers that are impossible without another cartridge

limited_locations = ['gift', 'gift-egg', 'only-one', 'pokeflute', 'squirt-bottle', 'wailmer-pail']  #effectively single-encounter, and therefore epic
limited_items = ['lax-incense', 'luck-incense', 'odd-incense']  #nonrenewable items, and therefore consuming them makes a pokemon at least epic

rare_items = ['dawn-stone', 'shiny-stone', 'dusk-stone', 'kings-rock',  #pickup
    'razor-fang']

annoying_conditions = ['swarm-yes']
annoying_locations = ['great-marsh']
annoying_items = ['thunder-stone', 'moon-stone', 'leaf-stone', 'water-stone', 'fire-stone', 'sun-stone',    #underground
    'razor-claw']    #common held item

known_evolution_triggers = ['shed']
simple_evolution_triggers = ['level-up', 'use-item']

species_counts = {
    'generation-i': [151, 78],
    'generation-ii': [251, 129],
    'generation-iii': [387, 202],
    'generation-iv': [493, 254],
    'generation-v': [649, 336],
    'generation-vi': [721, 373],
    'generation-vii': [809, 429],
    'generation-viii': [905, 460]
}

def get_friendly_name(obj):
    try:
        return friendly_names[obj['name']]
    except KeyError:
        json = requests.get(obj['url']).json()
        name = [name for name in json['names'] if name['language']['name'] == "en"][0]['name']
        friendly_names[obj['name']] = name
        return name

def get_species_name(species):
    try:
        return species_names[species]
    except KeyError:
        species_names[species] = requests.get("https://pokeapi.co/api/v2/pokemon-species/" + str(species) + "/").json()['name']
        return species_names[species]

def get_egg_group(species):
    try:
        return species_egg_group[species]
    except KeyError:
        species_egg_group[species] = requests.get("https://pokeapi.co/api/v2/pokemon-species/" + str(species) + "/").json()['egg_groups'][0]
        return species_egg_group[species]

routes = {}

def get_route(area):
    if area['name'] not in routes:
        routes[area['name']] = requests.get(area['url']).json()['location']
    return routes[area['name']]
    

def get_versions(encounter):
    return {version["version"]["name"] : version for version in encounter["version_details"]}

def get_gender(gender): #hardcoded because why not
    if gender == 1:
        return "female"
    elif gender == 2:
        return "male"
    else:
        return "genderless"

def load(version):
    json_file = open('data/global.json')
    universal_data = json.load(json_file)
    json_file = open(f'data/{version}.json')
    version_data = json.load(json_file)
    version_data = {**universal_data, **version_data}
    return version_data

class Version:
    def __init__(self, version, group, generation, regions):
        self.version = version
        self.group = group
        self.generation = generation
        self.regions = regions
        self.custom_data = load(version)
    def __getitem__(self, index):
        return self.custom_data[index]

version = input("Version: ")
main_version = None
support_versions = []
while version:
    version_group = requests.get(f"https://pokeapi.co/api/v2/version/{version}/").json()['version_group']['name']
    version_group_details = requests.get(f"https://pokeapi.co/api/v2/version-group/{version_group}/").json()
    generation = version_group_details['generation']['name']
    regions = [group['name'] for group in version_group_details['regions']]

    if main_version == None:
        main_version = Version(version, version_group, generation, regions)
    else:
        support_versions.append(Version(version, version_group, generation, regions))
    print(version, version_group, generation, regions)
    version = input("With help from (leave blank if done): ")

possible_mons = []

class Table_Builder:
    def __init__(self, name):
        self.row_index = 1
        self.max_columns = 6
        self.lines = []
        self.lines.append(f"<table class='{name}' style='width: 100%;'>")
        self.lines.append("<tbody>")
        self.lines.append("<tr>")
    def close(self):
        self.lines.append("</tr>")
        self.lines.append("</tbody>")
        self.lines.append("</table>")
    def export(self, filename):
        f = open(filename + ".html", "w")
        f.write("""<html>
    <head>
		<link rel="stylesheet" href="style.css">
    </head>""")
        f.write("\n".join(self.lines))
        f.write("</html>")
        f.close()
    def add_item(self, title, image, tag, details, color=None, alt=None):
        if alt == None:
            alt = title
        if self.row_index > self.max_columns:
            self.add_row()
            self.row_index = 1
        if color is None:
            self.lines.append("<td>")
        else:
            self.lines.append(f"<td bgcolor='{color}'>")
        self.lines.append(f"<p><strong>{title}</strong></p>")
        self.lines.append(f"<p><img src='{image}' alt='{alt}'/></p>")
        self.lines.append("<details>")
        self.lines.append(f"<summary>{tag}</summary>")
        for detail in details:
            self.lines.append(detail + "<br>")
        self.lines.append("</details>")
        self.row_index += 1
        self.lines.append("</td>")
    def add_row(self):
        self.lines.append("</tr>")
        self.lines.append("<tr>")
    def add_summary(self):  #TODO
        self.lines.append(f"<table class='{name}' style='width: 100%;'>")
        self.lines.append("<tbody>")
        self.lines.append("<tr>")
        self.lines.append("</tr>")
        self.lines.append("</tbody>")
        self.lines.append("</table>")

class Pokemon_Entry:
    def __init__(self, entry_number, name, rarity, details):
        self.entry_number = entry_number
        self.name = name
        self.rarity = rarity
        self.details = details
        
        self.queued_details = {}
    def add_details(self, details):
        self.details.append(details)
    def update_rarity(self, rarity, conditions=[], queue=None):
        if conditions:
            if queue and (self.rarity > rarity or queue not in self.queued_details.keys()):
                self.queued_details[queue] = conditions
            elif not queue:
                self.details.extend(conditions)
        self.rarity = min(self.rarity, rarity)
    def push_queue(self):
        for queue in self.queued_details.keys():
            self.details.extend(self.queued_details[queue])
        self.queued_details = {}
    def title(self):
        return "#" + str(self.entry_number) + " " + self.name.upper()
table_entries = []

def is_exclusive(species_name):
    exclusives = [entry for exclusive_group in main_version["exclusive-pokemon"].items() for entry in exclusive_group[1]]
    return species_name in exclusives

#STANDARD ENCOUNTERS
for mon in range(1,species_counts[generation][0]+1):
    mon_name = get_species_name(mon)
    json = requests.get("https://pokeapi.co/api/v2/pokemon/" + str(mon) + "/encounters").json()
    print("POKEDEX #", mon)
    rarity = IMPOSSIBLE
    outputs = []
    for encounter in json:
        local_rarity = IMPOSSIBLE
        versions = get_versions(encounter)
        if main_version.version in get_versions(encounter).keys():
            area = get_friendly_name(encounter['location_area'])
            location = get_friendly_name(get_route(encounter['location_area']))
            display = []
            invalid = True
            display.append([location, area])
            for variation in versions[main_version.version]['encounter_details']:
                #print(variation)
                trigger = get_friendly_name(variation['method'])
                min_level=variation['min_level']
                max_level=variation['max_level']
                
                if variation['method']['name'] in limited_locations:
                    display.append([trigger, f"{variation['chance']}% {min_level}-{max_level}"])
                    invalid = False
                    local_rarity = min(EPIC, local_rarity)
                    continue
                if len(variation['condition_values']) == 0: #no conditions, base rate
                    display.append([trigger, f"{variation['chance']}% {min_level}-{max_level}"])
                    invalid = False
                    local_rarity = min(UNCOMMON, local_rarity)
                else:
                    if any(set([value['name'] for value in variation['condition_values']]) & set(forbidden_conditions)):
                        continue
                    else:
                        invalid = False
                        local_rarity = min(UNCOMMON, local_rarity)
                    conditions = []
                    for condition in variation['condition_values']:
                        conditions.append(get_friendly_name(condition))
                    disp_conditions = ", ".join(conditions)
                    display.append([f"{trigger}, {disp_conditions} +{variation['chance']}% {min_level}-{max_level}"])
                
            #print(encounter)
            route = get_route(encounter['location_area'])['name']
            conditions = [value['name'] for value in variation['condition_values']]
            if (local_rarity == UNCOMMON and versions[main_version.version]['max_chance'] >= 10 and  #common criterion
                route not in annoying_locations and     #not forced to be uncommon, thanks to special rules/difficulty of arriving at certain location
                not any(set(conditions) & set(annoying_conditions))):   #not forced to be uncommon, thanks to encounter conditions
                local_rarity = min(COMMON, local_rarity)
            
            if is_exclusive(mon_name):
                local_rarity = max(EXOTIC, local_rarity)
            
            display.append([""])
            output = [" ".join(line) for line in display]
            if not invalid:
                outputs.append("<br>".join(output))
        rarity = min(rarity, local_rarity)
    new_entry = Pokemon_Entry(mon, mon_name, rarity, outputs)
    table_entries.append(new_entry)

def get_species(current_link_in_evolution_chain):
    url = current_link_in_evolution_chain['species']['url']
    return re.search("https://pokeapi.co/api/v2/pokemon-species/(.*)/", url).group(1)

def item_exists(item_name, main_version):
    item_json = requests.get(f"https://pokeapi.co/api/v2/item/{item_name}/").json()
    for game_index in item_json['game_indices']:
        if game_index['generation']['name'] == main_version.generation:
            return True
    return False

def evolution_difficulty(details):
    print(details)
    best_method_rarity = IMPOSSIBLE
    best_method_conditions = []
    for method in details:
        method_rarity = COMMON
        method_conditions = []
        
        if method['min_affection']:
            method_rarity = max(method_rarity, COMMON)    #affection is usually easy or cheesable
            method_conditions.append(f"With affection >= {method['min_affection']}")
        if method['min_happiness']:
            method_rarity = max(method_rarity, COMMON)    #synonym of affection
            method_conditions.append(f"With happiness >= {method['min_happiness']}")
        if method['turn_upside_down']:
            method_rarity = max(method_rarity, COMMON)    #it's not hard, just weird
            method_conditions.append("Turn device upside down")
        if method['party_type']:
            method_rarity = max(method_rarity, COMMON)    #closest there is to a rare type is dragon in gen I and fire in gen IV regional dex. they're not rare.
            method_conditions.append(f"With {method['part_type']} type in party")
        
        if method['needs_overworld_rain']:
            method_rarity = max(method_rarity, UNCOMMON)  #some games have time-dependent weather
            method_conditions.append(f"While raining")
        if method['min_level']:
            if method['min_level'] > 50:
                method_rarity = max(method_rarity, UNCOMMON)  #leveling up past level 50 is quite a tall order; most in-game battle arenas operate at level 50
                method_conditions.append(f"At very high level {method['min_level']}")
            else:
                method_conditions.append(f"At level {method['min_level']}")
        if method['relative_physical_stats'] is not None:
            method_rarity = max(method_rarity, UNCOMMON)    #hitmontop's balanced physical stats CAN be hard, but I haven't found it to be
            if method['relative_physical_stats'] < 0:
                method_conditions.append(f"With greater defense than attack")
            elif method['relative_physical_stats'] > 0:
                method_conditions.append(f"With greater attack than defense")
            else:
                method_conditions.append(f"With perfectly balanced attack and defense")
        if method['time_of_day']:
            method_rarity = max(method_rarity, UNCOMMON)    #could ask for morning, a small window of time that some people may not be up by
            method_conditions.append(f"At time {method['time_of_day']}")
        if method['gender']:
            method_rarity = max(method_rarity, UNCOMMON)  #some gender ratios make this method very slow
            method_conditions.append(f"Must be {get_gender(method['gender'])}")
        
        if method['min_beauty']:
            method_rarity = max(method_rarity, RARE)  #milotic, enough said.
            method_conditions.append(f"With beauty >= {method['min_beauty']}")
        
        if method['known_move']:
            method_rarity = max(method_rarity, UNCOMMON)      #lazy base case
            method_conditions.append(f"Knowing move {method['known_move']['name']}")
        if method['known_move_type']:
            method_rarity = max(method_rarity, COMMON)
            method_conditions.append(f"Knowing {method['known_move_type']} type move")
        
        if method['location']:  #some locations don't exist in all games
            get_friendly_name(get_route(encounter['location_area']))
            print(method['location'])
            location_object = requests.get(method['location']['url']).json()
            location_versions = location_object['game_indices']
            location_region = location_object['region']
            if main_version.generation not in [index['generation']['name'] for index in location_versions]:
                method_rarity = max(method_rarity, IMPOSSIBLE)
                method_conditions.append(f"At {method['location']['name']} outside of this generation")
            elif location_region['name'] not in regions:
                method_rarity = max(method_rarity, IMPOSSIBLE)
                method_conditions.append(f"At {method['location']['name']} outside of this region")
            else:
                method_rarity = max(method_rarity, COMMON)    #no required locations are hard to return to.
                method_conditions.append(f"At {method['location']['name']}")
        if method['party_species']:
            other_species = next(iter([entry for entry in table_entries if entry.name == method['party_species']['name']]), None)
            if other_species:
                method_rarity = max(method_rarity, other_species.rarity)    #the species you need may not be available in your game
                method_conditions.append(f"With {method['party_species']['name']} in party")
            else:
                method_rarity = max(method_rarity, IMPOSSIBLE)    #the species you need may not be available in your game
                method_conditions.append(f"With unobtainable {method['party_species']['name']} in party")
        if method['trade_species']:
            method_rarity = max(method_rarity, MYTHICAL)    #the species you ask for may not be available in the other game
            method_conditions.append(f"For a {method['trade_species']}")
        
        if method['held_item']:
            if method['held_item']['name'] in rare_items:
                method_rarity = max(method_rarity, RARE)
                method_conditions.append(f"Holding rare {method['held_item']['name']}")
            elif method['held_item']['name'] in annoying_items:
                method_rarity = max(method_rarity, UNCOMMON)
                method_conditions.append(f"Holding found {method['held_item']['name']}")
            else:
                method_rarity = max(method_rarity, MYTHICAL)      #item might be unobtainable
                method_conditions.append(f"Holding {method['held_item']['name']}")
        if method['item']:
            if method['item']['name'] in annoying_items:
                method_rarity = max(method_rarity, UNCOMMON)
                method_conditions.append(f"Using found {method['item']['name']}")
            elif method['item']['name'] in rare_items:
                method_rarity = max(method_rarity, RARE)
                method_conditions.append(f"Using rare {method['item']['name']}")
            elif not item_exists(method['item']['name'], main_version):
                method_rarity = max(method_rarity, NONEXISTANT)
                method_conditions.append(f"Using nonexistant item {method['item']['name']}")
            else:
                method_rarity = max(method_rarity, MYTHICAL)      #item might be unobtainable
                method_conditions.append(f"Using {method['item']['name']}")
        
        if method['trigger']['name'] in forbidden_evolution_triggers:
            method_rarity = max(method_rarity, IMPOSSIBLE)
            method_conditions.append(f"Requires trade")
        elif method['trigger']['name'] not in simple_evolution_triggers:
            if method['trigger']['name'] not in known_evolution_triggers:
                method_rarity = max(method_rarity, MYTHICAL)
            method_conditions.append(f"Triggered by {method['trigger']['name']}")
        
        if method_conditions == []:     #location specific pokemon are bugged in this way, always.
            break   #stop. this would otherwise include stone evolutions in their place, which don't work retroactively.
        
        if best_method_rarity >= method_rarity:
            best_method_rarity = min(best_method_rarity, method_rarity)
            best_method_conditions = method_conditions
    
    return (best_method_rarity, best_method_conditions)

# consider evolutions as it effects pokemon rarity.
# simple evolution simply passes the rarity up the chain.
# more complex methods (or perhaps even finite ones!) introduce a lower limit on how rare the pokemon can be.
def recursive_update(current_link_in_evolution_chain, last_mon = None):
    species = int(get_species(current_link_in_evolution_chain))
    entry = next(iter([entry for entry in table_entries if entry.entry_number == species]), None)
    if entry:   #the pokemon must exist to be worth updating rarity
        last_entry = next(iter([entry for entry in table_entries if entry.entry_number == last_mon]), None)
        
        previous_rarity = IMPOSSIBLE    #no previous entry means evolution must be impossible
        if last_entry:  #but if there was one...
            previous_rarity = last_entry.rarity #then it might be as good as the rarity of the previous (no better)
        
        print(entry.name, entry.rarity)
        evolution_rarity, conditions = evolution_difficulty(current_link_in_evolution_chain['evolution_details'])
        local_rarity = max(previous_rarity, evolution_rarity)
        if last_mon and conditions:     #there is something to evolve from, and a method to take
            conditions.insert(0, "Evolve from " + get_species_name(last_mon))
            entry.update_rarity(local_rarity, conditions, 'EVOLUTION')
    
    for next_link in current_link_in_evolution_chain['evolves_to']:
        recursive_update(next_link, species)

# consider breeding as it effects pokemon rarity.
# any pokemon that can lay eggs passes its rarity down the chain, with a few exceptions
# EPIC pokemon that can breed are clearly not one-off events, so they have their rarity reduced - by default to RARE.
# but there are cases where this doesn't make very much sense. the starters, as they exclude the other starters, are still EPIC.
# if the breeding requires a rare incense, then it may become rarer than COMMON.
def reversive_update(current_link_in_evolution_chain, initial_chain, item):
    species = int(get_species(current_link_in_evolution_chain))
    entry = next(iter([entry for entry in table_entries if entry.entry_number == species]), None)
    if entry:   #the pokemon must exist to be worth updating rarity
        rarity = entry.rarity
        if rarity == EPIC:     #only one can be found, and picking it does not exclude other pokemon.
            rarity = RARE     #depends on the rarity of the single encounter. in any case, it's spawn is at least renewable.
        print(entry.name, entry.rarity)
        
        egg_group = get_egg_group(species)
        print(egg_group)
        if egg_group['name'] != "no-eggs":
            
            child_chain = initial_chain
            if child_chain['is_baby']:
                child_species = int(get_species(child_chain))
                child_entry = next(iter([entry for entry in table_entries if entry.entry_number == child_species]), None)
                
                #check item rarity, and boost accordingly
                baby_rarity = rarity
                if item and item['name'] not in limited_items:
                    baby_rarity = max(baby_rarity, MYTHICAL)
                
                if child_entry:
                    if item:
                        child_entry.update_rarity(baby_rarity, [f"Breed from {get_species_name(species)} holding {item['name']}"], 'BREEDING')
                    else:
                        child_entry.update_rarity(rarity, [f"Breed from " + get_species_name(species)], 'BREEDING')
                
                if item:
                    child_chain = child_chain['evolves_to'][0]
            
            if not child_chain['is_baby']:  #should no longer be a baby, otherwise this is a dupe because there was no item
                child_species = int(get_species(child_chain))
                child_entry = next(iter([entry for entry in table_entries if entry.entry_number == child_species]), None)
                
                if child_entry:
                    child_entry.update_rarity(rarity, [f"Breed from " + get_species_name(species)], 'BREEDING')
    
    for next_link in current_link_in_evolution_chain['evolves_to']:
        reversive_update(next_link, initial_chain, item)

def item_rarity_at_least(rarity, item):
    for category_name,category_details in main_version['items'].items():
        if rarity_value(category_details['rarity']) < rarity: #more common than this group
            if item in category_details['list']:
                return False    #found a counterexample
    return True #no counterexample

#FOSSILS
for mon in main_version['crafting'].keys():
    associated_entry = next(iter([entry for entry in table_entries if entry.name == mon]), None)
    if associated_entry == None:    #mon does not exist yet
        continue
    items = main_version['crafting'][mon]
    if any([item_rarity_at_least(IMPOSSIBLE, item) for item in items]):
        associated_entry.update_rarity(IMPOSSIBLE, [f"Revive from unobtainable {','.join(items)}"], 'FOSSIL')
    elif any([item_rarity_at_least(EPIC, item) for item in items]):
        associated_entry.update_rarity(EPIC, [f"Revive from limited {','.join(items)}"], 'FOSSIL')
    elif any([item_rarity_at_least(RARE, item) for item in items]):
        associated_entry.update_rarity(RARE, [f"Revive from rare {','.join(items)}"], 'FOSSIL')
    elif any([item_rarity_at_least(UNCOMMON, item) for item in items]):
        associated_entry.update_rarity(UNCOMMON, [f"Revive from found {','.join(items)}"], 'FOSSIL')
    else:
        associated_entry.update_rarity(COMMON, [f"Revive from common {','.join(items)}"], 'FOSSIL')

#ENCOUNTERS NOT IN THE API
for encounter_name,encounter_details in main_version['unlisted-encounters'].items():
    for mon in encounter_details['list']:
        associated_entry = next(iter([entry for entry in table_entries if entry.name == mon]), None)
        if associated_entry == None:    #mon does not exist yet
            continue
        associated_entry.update_rarity(rarity_value(encounter_details['rarity']), [encounter_details['label']], 'EXTRANEOUS')

#GIVEAWAYS
for mon in main_version['giveaways']:
    associated_entry = next(iter([entry for entry in table_entries if entry.name == mon]), None)
    if associated_entry == None:    #mon does not exist yet
        continue
    associated_entry.update_rarity(MYTHICAL, ["Event"], 'GIVEAWAY')

#EVOLUTION AND BREEDING
for evolution_chain in range(1,species_counts[generation][1]+1):
    print(evolution_chain)
    request_result = requests.get(f"https://pokeapi.co/api/v2/evolution-chain/{evolution_chain}/")
    if not request_result:
        continue
    json = request_result.json()
    current = json['chain']
    recursive_update(current)
    if main_version['breeding']:    #can breed in this game (everything since gen II!)
        reversive_update(current, current, json['baby_trigger_item'])
        recursive_update(current)
    

table_builder = Table_Builder("pokedex-table")

for table_entry in table_entries:
    table_entry.push_queue()
    image_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/{main_version.generation}/{main_version.group}/{table_entry.entry_number}.png"
    if table_entry.rarity == COMMON:
        table_builder.add_item(table_entry.title(), image_url, "Locations", table_entry.details)
        possible_mons.append(table_entry.entry_number)
    elif table_entry.rarity == UNCOMMON:
        table_builder.add_item(table_entry.title(), image_url, "Details", table_entry.details, color='3DADFC')
        possible_mons.append(table_entry.entry_number)
    elif table_entry.rarity == RARE:
        table_builder.add_item(table_entry.title(), image_url, "Details", table_entry.details, color='34D93A')
        possible_mons.append(table_entry.entry_number)
    elif table_entry.rarity == EPIC:
        table_builder.add_item(table_entry.title(), image_url, "Details", table_entry.details, color='F0CF45')
        possible_mons.append(table_entry.entry_number)
    elif table_entry.rarity == EXOTIC:
        table_builder.add_item(table_entry.title(), image_url, "Not always!", table_entry.details, color='D95034')
        possible_mons.append(table_entry.entry_number)
    elif table_entry.rarity == MYTHICAL:
        table_builder.add_item(table_entry.title(), image_url, "Not anymore!", table_entry.details, color='A449FC')
        possible_mons.append(table_entry.entry_number)
    elif table_entry.rarity == IMPOSSIBLE:
        table_builder.add_item(table_entry.title(), image_url, "Cannot be caught!", table_entry.details, color='gray')
    else:
        table_builder.add_item(table_entry.title(), image_url, "Does not exist!", table_entry.details, color='424242')

table_builder.close()
table_builder.export(main_version.version)

print(possible_mons)
print(len(possible_mons))