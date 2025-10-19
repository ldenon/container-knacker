import os
from json_parser import JSONParser
from make_3d_to_2d_problem import StapelOptimierer
import subprocess



# load json and parse order
parser = JSONParser()
path = os.path.join(os.path.dirname(__file__), "optimized_output.json")
parser.read_json(path)

container_dim = parser.get_container_dimensions()
# Create a list of all objects in the json -> transform to rectangle or cylinder
# 200 objects for stacking PROPABLY TOO MUCH!!!
objects = parser.get_objects()
objects = objects[:12]


# inspect one example object
# example = objects[0]
# print(f"Example object: {example.name}, Form: {example.form}, Grundfläche: {example.grundflaeche:.2f} mm², Höhe: {example.hoehe} mm, Gewicht: {example.gewicht_kg} kg, params: {example.abmessungen}")
# check that all objects have valid groundarea
for obj in objects:
    # print(f"Object: {obj.name}, Form: {obj.form}, Grundfläche: {obj.grundflaeche:.2f} m², Höhe: {obj.hoehe} m, Gewicht: {obj.gewicht_kg} kg, params: {obj.abmessungen}")
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
placed_data = parser.read_placed_json_data(placed_file_path)
print("Placed data objects:")
placement_map = {d['name']: d['placement'] for d in placed_data}
print(placement_map["Stapel_1"].keys())
for d in placed_data:
    print(d["name"])    
# parser.create_stack_result_json(aggregated_stack_positions=placed_data, stacks_list=stack)