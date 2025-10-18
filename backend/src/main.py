import os
from json_parser import JSONParser
from make_3d_to_2d_problem import StapelOptimierer


# load json and parse order
parser = JSONParser()
path = os.path.join(os.path.dirname(__file__), "beispiel.json")
parser.read_json(path)
container_dim = parser.get_container_dimensions()
objects = parser.get_objects()

# go through objects and print grundflaeche
for obj in objects:
    # print(f"Object: {obj.name}, Form: {obj.form}, Grundfläche: {obj.grundflaeche:.2f} m², Höhe: {obj.hoehe} m, Gewicht: {obj.gewicht_kg} kg, params: {obj.abmessungen}")
    assert obj.grundflaeche > 0, f"Grundfläche should be > 0 for object"

print("Es sind insgesamt", len(objects), "Objekte zum Stapeln vorhanden.")
# 3D -> 2D projection and stacking logic would go here
stack_optimizer = StapelOptimierer(max_hoehe=container_dim.height, objekte=objects)
stack, gesamt_grundflaeche = stack_optimizer.loese_problem()
print("Optimized Stack:")
for level, objs in enumerate(stack):
    print(f"Level {level + 1}:")
    for obj in objs:
        print(f"container dimensions: {container_dim}")
        print(f"  - {obj.name} ({obj.form}, Grundfläche: {obj.grundflaeche:.2f} mm², Höhe: {obj.hoehe} m, Gewicht: {obj.gewicht_kg} kg)")
print(f"Gesamt Grundfläche aller Objekte im Stapel: {gesamt_grundflaeche:.2f} mm²")


stack_object_list = stack_optimizer.stapel_zu_objekten_aggregieren(stack)
print("Number of stacks", len(stack_object_list))
# convert stack to json
parser.create_object_list_from_stacks(stack_object_list)
# print the created objects from stack
print("Created objects from stack:")