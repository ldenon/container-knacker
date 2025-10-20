import os
from stack_administrator import stack_administrator
from json_parser import JSONParser
from make_3d_to_2d_problem import StapelOptimierer
import subprocess



# load json and parse order
parser = JSONParser()
path = os.path.join(os.path.dirname(__file__), "optimized_output.json")
parser.read_json(path)
container_dim = parser.get_container_dimensions()
print("Höhe des Containers in mm:", container_dim.height)
print("Länge des Containers in mm:", container_dim.length)
print("Breite des Containers in mm:", container_dim.width)

# Create a list of all objects in the json -> transform to rectangle or cylinder
# 200 objects for stacking PROPABLY TOO MUCH!!!
objects = parser.get_objects()
objects = objects[:40]


# inspect one example object
# example = objects[0]
# print(f"Example object: {example.name}, Form: {example.form}, Grundfläche: {example.grundflaeche:.2f} mm², Höhe: {example.hoehe} mm, Gewicht: {example.gewicht_kg} kg, params: {example.abmessungen}")
# check that all objects have valid groundarea
for obj in objects:
    print(f"id: {obj.id}, Form: {obj.form}, Grundfläche: {obj.grundflaeche:.2f} m², Höhe: {obj.hoehe} m, Gewicht: {obj.gewicht_kg} kg, params: {obj.abmessungen}")
    assert obj.grundflaeche > 0, f"Grundfläche should be > 0 for object"

print("Es sind insgesamt", len(objects), "Objekte zum Stapeln vorhanden.")
# 3D -> 2D projection and stacking logic would go here
stack_optimizer = StapelOptimierer(max_hoehe=container_dim.height, objekte=objects)


stack, gesamt_grundflaeche = stack_optimizer.loese_problem()
print("There are:", len(stack), "stacks")
for level, objs in enumerate(stack):
    print(f"Level {level + 1}:")
    print("There are ", len(objs), "stacked objects")
print(f"Gesamt Grundfläche aller Objekte im Stapel: {gesamt_grundflaeche:.2f} mm²")



stack_object_list = stack_optimizer.stapel_zu_objekten_aggregieren(stack)
print("Number of stacks", len(stack_object_list))
# convert stack to json and save as meine_Bestellung.json
parser.create_object_list_from_stacks(stack_object_list)


### Use Algorithm2d algorithm to create placed.json
## run algorithm2d as process
path = os.path.dirname(__file__)
comb_path = os.path.join(path, "algorithm2d.py")
subprocess.run(["python", comb_path])
## This should create placed.json file

path = os.path.dirname(__file__)
placed_file_path = os.path.join(path, "placed.json")
# print("Reading placed data from", placed_file_path)

stack_position = parser.read_placed_json_data(placed_file_path)
# Currently there are stacks that are too high -> due to confusions with mm, cm 
# this should be fixed -> when running the algorithm2d.py script separately it should work fine

container_width = float(container_dim.width)
container_length =float( container_dim.length)
myStckHandler = stack_administrator(stacks=stack, stack_positions=stack_position, container_width=container_width, container_length=container_length)
# myStckHandler.show_stacks()
# myStckHandler.show_stack_positions()
dict = myStckHandler.create_dict()
final_dir = parser.create_jsn_for_3d(dict)
print(final_dir)
# save final_dir as json
output_path = os.path.join(path, "final_3d_stacks.json")
parser.dictionary_to_json_file(final_dir, output_path)
"""

# placement_map = {d['name']: d['placement'] for d in stack_position}
# print(placement_map["Stapel_1"].keys())
# for d in stack_position:
    # print(d["name"])
# parser.create_stack_result_json(aggregated_stack_positions=placed_data, stacks_list=stack)
"""