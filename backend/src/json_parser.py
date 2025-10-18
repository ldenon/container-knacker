
import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

# Load the Objekt class directly from backend/transport_objects/3dimensional.py
import importlib.util
import sys
import os
# import the Objekt class from the 3dimensional.py file

@dataclass
class ContainerDim:
    length: float
    width: float
    height: float


class JSONParser:
    """JSON parser that returns ContainerDim and a list of Objekt instances.

    parse_order(file_path) -> (ContainerDim, List[Objekt])
    """

    @staticmethod
    def _map_form_to_type(form: Dict[str, Any]) -> str:
        f_type = form.get("type", "").lower()
        if f_type in ("rectangle", "rect", "quader", "box"):
            return "Quader"
        if f_type in ("cylinder", "zylinder"):
            return "Zylinder"
        # default fallback
        return "Quader"

    @staticmethod
    def parse_order(file_path: str):
        """Parse an order JSON and extract container dimensions and Objekt list.

        Returns
        -------
        (ContainerDim, List[Objekt])
        """
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        order = data.get("order") or data

        # Find a container to use: prefer one with use==true, else first
        containers = order.get("container_definitions", [])
        chosen: Optional[ContainerDim] = None
        for c in containers:
            if c.get("use"):
                dims = c.get("inner_dimensions", {})
                chosen = ContainerDim(
                    length=dims.get("length", 0),
                    width=dims.get("width", 0),
                    height=dims.get("height", 0),
                )
                break

        if chosen is None and containers:
            dims = containers[0].get("inner_dimensions", {})
            chosen = ContainerDim(
                length=dims.get("length", 0),
                width=dims.get("width", 0),
                height=dims.get("height", 0),
            )
        # Build Objekt list using the Projekt's Objekt class
        objs: List[Any] = []
        for o in order.get("objects", []):
            form = o.get("form", {})
            mapped = JSONParser._map_form_to_type(form)
            # prepare params and hoehe based on mapped type
            if mapped == "Zylinder":
                radius = form.get("radius")
                hoehe = form.get("height")
                params = [radius]
            else:  # Quader
                laenge = form.get("length")
                breite = form.get("width")
                hoehe = form.get("height")
                params = [laenge, breite]
            name = o.get("product_name", f"obj_{o.get('id')}")
            # Ensure numeric defaults if fields missing
            params = [p or 0 for p in params]
            hoehe = hoehe or 0
            obj = Objekt(name, mapped, params, hoehe)
            objs.append(obj)

        return chosen, objs
