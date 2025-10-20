
class stack_administrator:
    def __init__(self, stacks, stack_positions, container_width=1200, container_length=3000):
        """
        Create stack dictionary from stacks and their positions.
        Objects on the ground have stack_level -1!

        stacks: [
        {"stack1":
            {object1: {type: "rectangle", stack_level:-1, position: (x,y), dimensions: radius or (l,w), height: h},
             object2: {type: "rectangle", stack_level:-1, position: (x,y), dimensions: radius or (l,w), height: h},
        
        }
        ]
        
        Rotation is handled in this class. 

        Args:
            stacks (list): List of stack dictionaries.
            stack_positions (dict): Dictionary of stack positions.
        """
        self.stacks = stacks
        self.stack_positions = stack_positions
        self.container_width = container_width
        self.container_length = container_length
    
    def show_stacks(self):
        """show the first stack"""
        if not self.stacks:
            print("No stacks available.")
            return

        print(len(self.stacks), "stacks available.")
        # go through first stack and print object details
        first_stack = self.stacks[0]
        print("First stack has", len(first_stack), "objects.")
        for obj in first_stack:
            print(f"ID: {obj.id}, Type: {obj.form}, Dimensions: {obj.abmessungen}, Height: {obj.hoehe}")
    
    def show_stack_positions(self):
        """show stack positions"""
        print("Stack positions:")
        for i, pos in enumerate(self.stack_positions):
            print(f"Stack {i+1}: Position: {pos}")

    def get_obj_pos_in_stack(self, ground_x, ground_y,form,width, height, z):
        # if quader then adjust position
        if form == "Quader":
            position = {
                "x": ground_x+width/2,
                "y": ground_y+height/2,
                "z": z
            }
        else:
            position = {
                    "x": ground_x,
                    "y": ground_y,
                    "z": z
                }
        translation_x = self.container_width / 2
        translation_y = self.container_length / 2
        position["x"] -= translation_x
        position["y"] -= translation_y
        return position
    
    def get_width_length_for_rotation(self, obj, rotation):
        # return length, width
        length = obj.abmessungen['laenge']
        width = obj.abmessungen['breite']
        if (rotation/90) % 2 == 1:
            # change if rotated
            return width, length
        return length, width

    def create_dict(self):
        # should contain {"Stack_1": {object1_data}, "Stack_2": {object2_data}, ...}
        stacks = []
        # go through stacks
        assert len(self.stacks) == len(self.stack_positions), "Number of stacks and positions must match"
        for i in range(len(self.stack_positions)):
            ground_position_x = self.stack_positions[i].get("placement").get("position").get("x", 0)
            ground_position_y = self.stack_positions[i].get("placement").get("position").get("y", 0)
            stack_name = self.stack_positions[i].get("name", f"Stapel_{i+1}")
            ground_form = self.stacks[i][0].form  # form of the bottom object
            ground_rotation = self.stack_positions[i].get("placement").get("rotation", 0).get("z_axis", 0)
            stack_dict = {"name": stack_name}
            # go through objects in stack
            stack_objects = []
            for j, obj in enumerate(self.stacks[i]):
                # determine object position
                if j == 0:
                    # object on ground
                    stack_level = -1
                    position = self.get_obj_pos_in_stack(
                        ground_x=ground_position_x,
                        ground_y=ground_position_y,
                        form=ground_form,
                        width=self.stacks[i][0].abmessungen.get('breite',0),
                        height=self.stacks[i][0].abmessungen.get('laenge',0),
                        z=0,
                    )
                else:
                    # object on top of previous object
                    position = self.get_obj_pos_in_stack(
                        ground_x=ground_position_x,
                        ground_y=ground_position_y,
                        form=ground_form,
                        width=self.stacks[i][0].abmessungen.get('breite',0),
                        height=self.stacks[i][0].abmessungen.get('laenge',0),
                        z=sum(o.hoehe for o in self.stacks[i][:j]),
                    )
                    # stack level is id of object in stack at position j-1
                    stack_level = self.stacks[i][j - 1].id
                if obj.form == "Quader":
                    length, width = self.get_width_length_for_rotation(obj, ground_rotation)
                    obj.abmessungen['laenge'] = length
                    obj.abmessungen['breite'] = width
                    
                obj_data = {
                    "id": obj.id,
                    "type": obj.form,
                    "dimensions": obj.abmessungen,
                    "height": obj.hoehe,
                    "weight_kg": obj.gewicht_kg,
                    "stack_level": stack_level,
                    "position": position
                }
                stack_objects.append(obj_data)

            stack_dict["objects"] = stack_objects
            stacks.append(stack_dict)
        return stacks
