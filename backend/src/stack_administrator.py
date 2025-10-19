
class stack_administrator:
    def __init__(self, stacks, stack_positions):
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
    
    def show_stacks(self):
        """show the first stack"""
        if not self.stacks:
            print("No stacks available.")
            return

        first_stack = self.stacks[0]
        for stack_name, objects in first_stack.items():
            print(f"Stack: {stack_name}")
            for obj_name, obj_info in objects.items():
                print(f"  Object: {obj_name}, Info: {obj_info}")
    
