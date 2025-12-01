from flask import Flask, jsonify, render_template, Response
import requests
import logging
import xml.etree.ElementTree as ET

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Jolokia endpoint URL
JOLOKIA_URL = "http://localhost:8080/actuator/jolokia"


def jolokia_request(mbean, operation=None, attribute=None, arguments=None):
    """
    Helper function to make Jolokia requests

    Args:
        mbean: The MBean name
        operation: Optional operation to execute
        attribute: Optional attribute to read
        arguments: Optional arguments for operation

    Returns:
        The response value from Jolokia
    """
    payload = {
        "type": "exec" if operation else "read",
        "mbean": mbean
    }

    if operation:
        payload["operation"] = operation
        if arguments:
            payload["arguments"] = arguments

    if attribute:
        payload["attribute"] = attribute

    try:
        response = requests.post(JOLOKIA_URL, json=payload)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != 200:
            logger.error(f"Jolokia error: {data}")
            return None

        return data.get("value")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None


@app.route('/')
def index():
    """Home page with simple documentation"""
    return render_template('index.html')


@app.route('/routes')
def get_routes():
    """Get list of all Camel routes"""
    logger.info("Fetching all routes...")

    # Search for all Camel route MBeans
    # The pattern matches all route MBeans in Camel
    search_payload = {
        "type": "search",
        "mbean": "org.apache.camel:type=routes,*"
    }

    try:
        response = requests.post(JOLOKIA_URL, json=search_payload)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != 200:
            return jsonify({"error": "Failed to fetch routes", "details": data}), 500

        mbeans = data.get("value", [])

        # Extract route IDs from MBean names
        routes = []
        for mbean in mbeans:
            # MBean format: org.apache.camel:context=camel-1,type=routes,name="route-id"
            parts = mbean.split(',')
            for part in parts:
                if part.startswith('name='):
                    route_id = part.split('=')[1].strip('"')
                    routes.append(route_id)
                    break

        logger.info(f"Found {len(routes)} routes: {routes}")

        return jsonify({
            "routes": routes,
            "count": len(routes)
        })

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return jsonify({"error": "Failed to connect to Jolokia", "details": str(e)}), 500


@app.route('/route/<route_id>')
def get_route_details(route_id):
    """Get detailed information about a specific route"""
    logger.info(f"Fetching details for route: {route_id}")

    # First, we need to find the exact MBean name for this route
    search_payload = {
        "type": "search",
        "mbean": f"org.apache.camel:type=routes,name=\"{route_id}\",*"
    }

    try:
        response = requests.post(JOLOKIA_URL, json=search_payload)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != 200:
            return jsonify({"error": "Failed to search for route", "details": data}), 500

        mbeans = data.get("value", [])

        if not mbeans:
            return jsonify({"error": f"Route '{route_id}' not found"}), 404

        # Use the first matching MBean
        mbean_name = mbeans[0]
        logger.info(f"Found MBean: {mbean_name}")

        # Read all attributes of the route MBean
        read_payload = {
            "type": "read",
            "mbean": mbean_name
        }

        response = requests.post(JOLOKIA_URL, json=read_payload)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != 200:
            return jsonify({"error": "Failed to read route details", "details": data}), 500

        route_info = data.get("value", {})

        # Get the route definition (XML)
        # Use () suffix to specify the no-argument signature for overloaded operations
        route_definition = jolokia_request(mbean_name, operation="dumpRouteAsXml()")

        # Get processors/steps for this route
        camel_context = route_info.get("CamelId", "camel-1")
        processors_search = {
            "type": "search",
            "mbean": "org.apache.camel:type=processors,*"
        }

        response = requests.post(JOLOKIA_URL, json=processors_search)
        response.raise_for_status()
        data = response.json()

        processors = []
        if data.get("status") == 200:
            processor_mbeans = data.get("value", [])

            for processor_mbean in processor_mbeans:
                # Read processor details
                proc_read = {
                    "type": "read",
                    "mbean": processor_mbean
                }

                proc_response = requests.post(JOLOKIA_URL, json=proc_read)
                proc_response.raise_for_status()
                proc_data = proc_response.json()

                if proc_data.get("status") == 200:
                    proc_info = proc_data.get("value", {})

                    # Only include processors that belong to this route
                    if proc_info.get("RouteId") == route_id:
                        processor_detail = {
                            "processorId": proc_info.get("ProcessorId"),
                            "processorName": proc_info.get("ProcessorName"),
                            "index": proc_info.get("Index"),
                            "level": proc_info.get("Level"),
                            "state": proc_info.get("State"),
                            "mbean": processor_mbean,
                            "statistics": {
                                "exchangesTotal": proc_info.get("ExchangesTotal"),
                                "exchangesCompleted": proc_info.get("ExchangesCompleted"),
                                "exchangesFailed": proc_info.get("ExchangesFailed"),
                                "minProcessingTime": proc_info.get("MinProcessingTime"),
                                "maxProcessingTime": proc_info.get("MaxProcessingTime"),
                                "meanProcessingTime": proc_info.get("MeanProcessingTime"),
                                "totalProcessingTime": proc_info.get("TotalProcessingTime"),
                                "lastProcessingTime": proc_info.get("LastProcessingTime")
                            }
                        }

                        # Add processor-specific attributes
                        if proc_info.get("ProcessorName") == "log":
                            processor_detail["message"] = proc_info.get("Message")
                            processor_detail["loggingLevel"] = proc_info.get("LoggingLevel")
                            processor_detail["logName"] = proc_info.get("LogName")
                        elif proc_info.get("ProcessorName") == "setBody":
                            processor_detail["expression"] = proc_info.get("Expression")
                            processor_detail["expressionLanguage"] = proc_info.get("ExpressionLanguage")

                        processors.append(processor_detail)

            # Sort processors by index
            processors.sort(key=lambda x: x.get("index", 0))

        logger.info(f"Found {len(processors)} processors for route {route_id}")

        # Construct a comprehensive response
        result = {
            "routeId": route_id,
            "mbean": mbean_name,
            "state": route_info.get("State"),
            "uptime": route_info.get("Uptime"),
            "camelId": route_info.get("CamelId"),
            "description": route_info.get("Description"),
            "endpointUri": route_info.get("EndpointUri"),
            "statistics": {
                "exchangesTotal": route_info.get("ExchangesTotal"),
                "exchangesCompleted": route_info.get("ExchangesCompleted"),
                "exchangesFailed": route_info.get("ExchangesFailed"),
                "failuresHandled": route_info.get("FailuresHandled"),
                "redeliveries": route_info.get("Redeliveries"),
                "externalRedeliveries": route_info.get("ExternalRedeliveries"),
                "minProcessingTime": route_info.get("MinProcessingTime"),
                "maxProcessingTime": route_info.get("MaxProcessingTime"),
                "meanProcessingTime": route_info.get("MeanProcessingTime"),
                "totalProcessingTime": route_info.get("TotalProcessingTime"),
                "lastProcessingTime": route_info.get("LastProcessingTime"),
                "deltaProcessingTime": route_info.get("DeltaProcessingTime")
            },
            "properties": route_info.get("RouteProperties"),
            "hasCustomIdAssigned": route_info.get("HasCustomIdAssigned"),
            "supportsRestart": route_info.get("SupportsRestart"),
            "routeDefinition": route_definition,
            "processors": processors
        }

        return jsonify(result)

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return jsonify({"error": "Failed to connect to Jolokia", "details": str(e)}), 500


@app.route('/route/<route_id>/graph')
def get_route_graph(route_id):
    """Generate SVG visualization of the route"""
    logger.info(f"Generating graph for route: {route_id}")

    # Get route details from the existing endpoint logic
    # First, find the exact MBean name for this route
    search_payload = {
        "type": "search",
        "mbean": f"org.apache.camel:type=routes,name=\"{route_id}\",*"
    }

    try:
        response = requests.post(JOLOKIA_URL, json=search_payload)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != 200:
            return jsonify({"error": "Failed to search for route", "details": data}), 500

        mbeans = data.get("value", [])

        if not mbeans:
            return jsonify({"error": f"Route '{route_id}' not found"}), 404

        # Use the first matching MBean
        mbean_name = mbeans[0]

        # Read route attributes
        read_payload = {
            "type": "read",
            "mbean": mbean_name
        }

        response = requests.post(JOLOKIA_URL, json=read_payload)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != 200:
            return jsonify({"error": "Failed to read route details", "details": data}), 500

        route_info = data.get("value", {})
        endpoint_uri = route_info.get("EndpointUri")

        # Get the route XML definition to extract the "from" element
        route_xml = jolokia_request(mbean_name, operation="dumpRouteAsXml()")

        # Get processors
        processors_search = {
            "type": "search",
            "mbean": "org.apache.camel:type=processors,*"
        }

        response = requests.post(JOLOKIA_URL, json=processors_search)
        response.raise_for_status()
        data = response.json()

        processors = []
        if data.get("status") == 200:
            processor_mbeans = data.get("value", [])

            for processor_mbean in processor_mbeans:
                proc_read = {
                    "type": "read",
                    "mbean": processor_mbean
                }

                proc_response = requests.post(JOLOKIA_URL, json=proc_read)
                proc_response.raise_for_status()
                proc_data = proc_response.json()

                if proc_data.get("status") == 200:
                    proc_info = proc_data.get("value", {})

                    if proc_info.get("RouteId") == route_id:
                        processor_detail = {
                            "processorId": proc_info.get("ProcessorId"),
                            "processorName": proc_info.get("ProcessorName"),
                            "index": proc_info.get("Index"),
                        }

                        if proc_info.get("ProcessorName") == "log":
                            processor_detail["message"] = proc_info.get("Message")
                            processor_detail["loggingLevel"] = proc_info.get("LoggingLevel")
                        elif proc_info.get("ProcessorName") == "setBody":
                            processor_detail["expression"] = proc_info.get("Expression")
                            processor_detail["expressionLanguage"] = proc_info.get("ExpressionLanguage")

                        processors.append(processor_detail)

            processors.sort(key=lambda x: x.get("index", 0))

        # Parse XML to get the "from" element
        from_id = None
        from_uri = endpoint_uri
        if route_xml:
            try:
                root = ET.fromstring(route_xml)
                # Handle namespace
                ns = {'camel': 'http://camel.apache.org/schema/xml-io'}
                from_elem = root.find('.//camel:from', ns)
                if from_elem is None:
                    from_elem = root.find('.//from')  # Try without namespace
                if from_elem is not None:
                    from_id = from_elem.get('id', 'from')
                    from_uri = from_elem.get('uri', endpoint_uri)
            except Exception as e:
                logger.warning(f"Failed to parse route XML: {e}")
                from_id = "from"

        # Generate SVG - check if we have choice or multicast elements
        has_choice = any(p.get('processorName') == 'choice' for p in processors)
        has_multicast = any(p.get('processorName') == 'multicast' for p in processors)

        if (has_choice or has_multicast) and route_xml:
            # Use XML-based branching visualizer
            svg = generate_branching_route_svg(route_id, route_xml, processors)
        else:
            # Use sequential visualizer
            svg = generate_route_svg(route_id, from_id or "from", from_uri, processors, route_xml)

        if svg is None:
            return jsonify({"error": "Failed to generate SVG"}), 500

        return Response(svg, mimetype='image/svg+xml')

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return jsonify({"error": "Failed to connect to Jolokia", "details": str(e)}), 500


def generate_branching_route_svg(route_id, route_xml, processors):
    """Generate SVG visualization for routes with choice/branching"""
    try:
        root = ET.fromstring(route_xml)
        ns = {'camel': 'http://camel.apache.org/schema/xml-io'}

        # SVG configuration
        box_width = 250
        box_height = 70
        start_x = 50
        start_y = 50
        arrow_height = 30
        branch_spacing = 350  # Horizontal spacing between branches

        # Build processor map for quick lookup
        proc_map = {p['processorId']: p for p in processors}

        # Parse route structure
        from_elem = root.find('.//camel:from', ns) or root.find('.//from')
        choice_elem = root.find('.//camel:choice', ns) or root.find('.//choice')
        multicast_elem = root.find('.//camel:multicast', ns) or root.find('.//multicast')

        # Determine branch element type
        branch_elem = choice_elem if choice_elem is not None else multicast_elem
        branch_tag = 'choice' if choice_elem is not None else 'multicast'

        # Get elements before branching element
        before_choice = []
        for child in root:
            if child.tag.endswith('from'):
                continue
            if child.tag.endswith(('choice', 'multicast')):
                break
            before_choice.append(child)

        # Get elements after branching element
        after_choice = []
        found_branch = False
        for child in root:
            if child.tag.endswith(('choice', 'multicast')):
                found_branch = True
                continue
            if found_branch:
                after_choice.append(child)

        # Get branches
        branches = []
        if choice_elem is not None:
            # Handle choice branches
            when_elems = choice_elem.findall('.//camel:when', ns) or choice_elem.findall('.//when')
            otherwise_elem = choice_elem.find('.//camel:otherwise', ns) or choice_elem.find('.//otherwise')

            for i, when_elem in enumerate(when_elems):
                branch = {'label': f'when #{i+1}', 'elements': list(when_elem)}
                branches.append(branch)

            if otherwise_elem is not None:
                branch = {'label': 'otherwise', 'elements': list(otherwise_elem)}
                branches.append(branch)
        elif multicast_elem is not None:
            # Handle multicast branches - each direct child "to" is a branch
            to_elems = multicast_elem.findall('.//camel:to', ns) or multicast_elem.findall('.//to')
            # Filter to only direct children
            to_elems = [elem for elem in multicast_elem if elem.tag.endswith('to')]

            for i, to_elem in enumerate(to_elems):
                uri = to_elem.get('uri', '')
                branch = {'label': f'branch {i+1}: {uri}', 'elements': [to_elem], 'uri': uri}
                branches.append(branch)

        # Calculate dimensions
        max_branch_length = max([len(b['elements']) for b in branches]) if branches else 0
        num_branches = len(branches)

        branch_height = max_branch_length * (box_height + arrow_height) if max_branch_length > 0 else box_height
        total_width = start_x * 2 + max(box_width, num_branches * branch_spacing)
        current_y = start_y

        # Calculate before/after heights
        before_height = len(before_choice) * (box_height + arrow_height)
        after_height = len(after_choice) * (box_height + arrow_height)

        # Initial height estimate (will be updated at the end)
        total_height = current_y + (box_height + arrow_height) + before_height + branch_height + after_height + 500

        # Start SVG (we'll update the height later)
        svg_parts = [
            f'<svg width="{total_width}" height="{total_height}" xmlns="http://www.w3.org/2000/svg">',
            '<defs>',
            '<style>',
            '.box { stroke: #333; stroke-width: 2; }',
            '.from-box { fill: #4CAF50; }',
            '.log-box { fill: #2196F3; }',
            '.setbody-box { fill: #FF9800; }',
            '.choice-box { fill: #9C27B0; }',
            '.multicast-box { fill: #673AB7; }',
            '.route-call-box { fill: #757575; }',
            '.setproperty-box { fill: #00BCD4; }',
            '.default-box { fill: #9E9E9E; }',
            '.box-text { fill: white; font-family: Arial, sans-serif; font-size: 14px; font-weight: bold; }',
            '.box-detail { fill: white; font-family: Arial, sans-serif; font-size: 11px; }',
            '.arrow { stroke: #333; stroke-width: 2; fill: none; marker-end: url(#arrowhead); }',
            '.branch-label { fill: #333; font-family: Arial, sans-serif; font-size: 12px; font-weight: bold; }',
            'a { cursor: pointer; }',
            'a:hover .route-call-box { fill: #555555; }',
            '</style>',
            '<marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">',
            '<polygon points="0 0, 10 3, 0 6" fill="#333" />',
            '</marker>',
            '</defs>',
            f'<text x="{total_width/2}" y="25" text-anchor="middle" style="font-family: Arial; font-size: 18px; font-weight: bold; fill: #333;">Route: {route_id}</text>',
        ]

        center_x = total_width / 2

        # Draw "from" box
        if from_elem is not None:
            from_id = from_elem.get('id', 'from')
            from_uri = from_elem.get('uri', '')
            box_parts, actual_height = draw_box(center_x - box_width/2, current_y, box_width, box_height,
                                       from_id, "from", from_uri, "from-box")
            svg_parts.extend(box_parts)
            current_y += actual_height + arrow_height
            svg_parts.append(f'<line x1="{center_x}" y1="{current_y - arrow_height}" x2="{center_x}" y2="{current_y}" class="arrow" />')

        # Draw elements before choice
        for elem in before_choice:
            elem_id = elem.get('id', '')
            elem_tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            detail = get_element_detail(elem, elem_tag, proc_map.get(elem_id, {}))
            box_class = get_box_class(elem_tag, elem)
            route_link = get_route_link_from_element(elem, elem_tag)

            box_parts, actual_height = draw_box(center_x - box_width/2, current_y, box_width, box_height,
                                       elem_id, elem_tag, detail, box_class, route_link)
            svg_parts.extend(box_parts)
            current_y += actual_height + arrow_height
            svg_parts.append(f'<line x1="{center_x}" y1="{current_y - arrow_height}" x2="{center_x}" y2="{current_y}" class="arrow" />')

        # Draw choice/multicast diamond/box
        choice_y = current_y
        if branch_elem is not None:
            branch_id = branch_elem.get('id', branch_tag)
            branch_box_class = f"{branch_tag}-box"
            box_parts, actual_height = draw_box(center_x - box_width/2, current_y, box_width, box_height,
                                       branch_id, branch_tag, f"{len(branches)} branches", branch_box_class)
            svg_parts.extend(box_parts)
            current_y += actual_height + arrow_height

        # Draw branches
        branch_start_y = current_y
        branch_end_positions = []  # Track actual end position of each branch

        if branches:
            # Calculate branch positions
            total_branch_width = (num_branches - 1) * branch_spacing
            start_branch_x = center_x - total_branch_width / 2

            for i, branch in enumerate(branches):
                branch_x = start_branch_x + i * branch_spacing
                branch_y = branch_start_y

                # Draw arrow from choice to branch
                svg_parts.append(f'<line x1="{center_x}" y1="{choice_y + box_height}" x2="{branch_x}" y2="{branch_y}" class="arrow" />')

                # Draw branch label
                svg_parts.append(f'<text x="{branch_x}" y="{branch_y - 10}" text-anchor="middle" class="branch-label">{branch["label"]}</text>')

                # Draw branch elements
                for elem in branch['elements']:
                    elem_id = elem.get('id', '')
                    elem_tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

                    # No special handling needed - just render the element normally

                    # Regular element (not a multicast direct: to)
                    detail = get_element_detail(elem, elem_tag, proc_map.get(elem_id, {}))
                    box_class = get_box_class(elem_tag, elem)
                    route_link = get_route_link_from_element(elem, elem_tag)

                    box_parts, actual_height = draw_box(branch_x - box_width/2, branch_y, box_width, box_height,
                                               elem_id, elem_tag, detail, box_class, route_link)
                    svg_parts.extend(box_parts)
                    branch_y += actual_height
                    # Only add arrow between elements
                    if branch['elements'].index(elem) < len(branch['elements']) - 1:
                        branch_y += arrow_height
                        svg_parts.append(f'<line x1="{branch_x}" y1="{branch_y - arrow_height}" x2="{branch_x}" y2="{branch_y}" class="arrow" />')

                # Store the actual end position of this branch (bottom of last box)
                branch_end_positions.append(branch_y)

            # Find the maximum branch end Y
            max_branch_end_y = max(branch_end_positions) if branch_end_positions else branch_start_y
            current_y = max_branch_end_y

            # Draw merge arrows from all branches to center
            merge_point_y = current_y + arrow_height
            for i in range(num_branches):
                branch_x = start_branch_x + i * branch_spacing
                svg_parts.append(f'<line x1="{branch_x}" y1="{branch_end_positions[i]}" x2="{center_x}" y2="{merge_point_y}" class="arrow" />')

            # Position next element at the merge point
            current_y = merge_point_y

        # Draw elements after choice
        for elem in after_choice:
            elem_id = elem.get('id', '')
            elem_tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            detail = get_element_detail(elem, elem_tag, proc_map.get(elem_id, {}))
            box_class = get_box_class(elem_tag, elem)
            route_link = get_route_link_from_element(elem, elem_tag)

            box_parts, actual_height = draw_box(center_x - box_width/2, current_y, box_width, box_height,
                                       elem_id, elem_tag, detail, box_class, route_link)
            svg_parts.extend(box_parts)
            current_y += actual_height
            if after_choice.index(elem) < len(after_choice) - 1:
                current_y += arrow_height
                svg_parts.append(f'<line x1="{center_x}" y1="{current_y - arrow_height}" x2="{center_x}" y2="{current_y}" class="arrow" />')

        # Update SVG height based on actual content
        actual_height = current_y + 50  # Add some bottom padding
        svg_parts[0] = f'<svg width="{total_width}" height="{actual_height}" xmlns="http://www.w3.org/2000/svg">'

        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)

    except Exception as e:
        logger.error(f"Failed to generate branching SVG: {e}")
        return None


def get_element_detail(elem, elem_tag, proc_info):
    """Extract detail text from XML element"""
    if elem_tag == 'log':
        return elem.get('message', proc_info.get('message', ''))
    elif elem_tag == 'setBody':
        const_elem = elem.find('.//constant') or elem.find('.//{http://camel.apache.org/schema/xml-io}constant')
        if const_elem is not None and const_elem.text:
            return f"constant: {const_elem.text}"
        return proc_info.get('expression', '')
    elif elem_tag == 'setProperty':
        return f"name: {elem.get('name', '')}"
    elif elem_tag == 'to':
        uri = elem.get('uri', '')
        if uri.startswith('direct:'):
            route_name = uri.replace('direct:', '')
            return f"→ {route_name}"
        return f"URI: {uri}"
    return ""


def get_box_class(elem_tag, elem=None):
    """Get CSS class for element type"""
    elem_tag_lower = elem_tag.lower()
    if elem_tag_lower in ['log', 'setbody', 'choice', 'setproperty']:
        return f"{elem_tag_lower}-box"
    # Special handling for "to" elements pointing to direct routes
    if elem_tag_lower == 'to' and elem is not None:
        uri = elem.get('uri', '')
        if uri.startswith('direct:'):
            return "route-call-box"
    return "default-box"


def generate_route_svg(route_id, from_id, from_uri, processors, route_xml=None):
    """Generate SVG visualization - delegates to proper handler based on route structure"""
    return generate_sequential_route_svg(route_id, from_id, from_uri, processors, route_xml)


def fetch_route_by_uri(uri):
    """Fetch route definition by direct URI (e.g., direct:hello -> hello-route)"""
    logger.info(f"Attempting to fetch route for URI: {uri}")

    if not uri.startswith('direct:'):
        logger.info(f"URI {uri} does not start with 'direct:', skipping")
        return None

    # Extract route name from direct URI
    route_name = uri.replace('direct:', '')
    # Search for route by endpoint URI
    search_payload = {
        "type": "search",
        "mbean": f"org.apache.camel:type=routes,*"
    }

    try:
        response = requests.post(JOLOKIA_URL, json=search_payload)
        data = response.json()
        if data.get("status") != 200:
            logger.error(f"Failed to search routes: {data}")
            return None

        mbeans = data.get("value", [])
        logger.info(f"Found {len(mbeans)} route MBeans to check for URI {uri}")

        # Find the route MBean with matching EndpointUri
        for mbean in mbeans:
            read_payload = {"type": "read", "mbean": mbean}
            resp = requests.post(JOLOKIA_URL, json=read_payload)
            route_data = resp.json()

            if route_data.get("status") == 200:
                route_info = route_data.get("value", {})
                endpoint_uri = route_info.get("EndpointUri")
                logger.info(f"Checking MBean endpoint: '{endpoint_uri}' against '{uri}'")

                # Normalize URIs: direct://hello -> direct:hello
                normalized_endpoint_uri = endpoint_uri.replace('://', ':') if endpoint_uri else None
                normalized_uri = uri.replace('://', ':')

                if normalized_endpoint_uri == normalized_uri:
                    logger.info(f"Found matching route for {uri}: {mbean}")
                    # Found the route, get its XML definition
                    route_xml = jolokia_request(mbean, operation="dumpRouteAsXml()")
                    if route_xml:
                        logger.info(f"Successfully fetched XML for {uri}")
                        return route_xml
                    else:
                        logger.error(f"Failed to fetch XML for {uri}")
                        return None

        logger.info(f"No matching route found for URI {uri}")
    except Exception as e:
        logger.error(f"Error fetching route for URI {uri}: {e}")

    return None


def parse_route_processors(route_xml):
    """Parse route XML and extract processors (excluding from)"""
    try:
        root = ET.fromstring(route_xml)
        processors = []

        # Iterate through all children except 'from'
        for child in root:
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if tag != 'from':
                processors.append({
                    'element': child,
                    'tag': tag,
                    'id': child.get('id', ''),
                    'uri': child.get('uri', '')
                })

        return processors
    except Exception as e:
        logger.error(f"Error parsing route XML: {e}")
        return []


def render_inlined_route_with_branching(called_route_xml, branch_x, branch_y, box_width, box_height, arrow_height, proc_map):
    """Render an inlined route that may contain choice/multicast elements with proper branching.

    Returns: (svg_parts, final_y)
    """
    try:
        ns = {'camel': 'http://camel.apache.org/schema/xml-io'}
        root = ET.fromstring(called_route_xml)
        svg_parts = []
        current_y = branch_y

        # Check if route has choice or multicast
        choice_elem = root.find('.//camel:choice', ns) or root.find('.//choice')
        multicast_elem = root.find('.//camel:multicast', ns) or root.find('.//multicast')

        if choice_elem is None and multicast_elem is None:
            # No branching - render sequentially
            inlined_procs = parse_route_processors(called_route_xml)
            for idx, inlined_proc in enumerate(inlined_procs):
                inlined_tag = inlined_proc['tag']
                inlined_elem = inlined_proc['element']
                inlined_detail = get_element_detail(inlined_elem, inlined_tag, proc_map.get(inlined_proc['id'], {}))
                inlined_box_class = get_box_class(inlined_tag, inlined_elem)
                route_link = get_route_link_from_element(inlined_elem, inlined_tag)

                box_parts, actual_height = draw_box(branch_x - box_width/2, current_y, box_width, box_height,
                                           inlined_elem.get('id', ''), inlined_tag, inlined_detail, inlined_box_class, route_link)
                svg_parts.extend(box_parts)
                current_y += actual_height
                # Only add arrow if not the last inlined processor
                if idx < len(inlined_procs) - 1:
                    current_y += arrow_height
                    svg_parts.append(f'<line x1="{branch_x}" y1="{current_y - arrow_height}" x2="{branch_x}" y2="{current_y}" class="arrow" />')
            return svg_parts, current_y

        # Has branching - split into before, branching, after
        branch_elem = choice_elem if choice_elem is not None else multicast_elem
        branch_tag = 'choice' if choice_elem is not None else 'multicast'

        # Get elements before branching
        before_branch = []
        for child in root:
            if child.tag.endswith('from'):
                continue
            if child.tag.endswith(('choice', 'multicast')):
                break
            before_branch.append(child)

        # Get elements after branching
        after_branch = []
        found_branch = False
        for child in root:
            if child.tag.endswith(('choice', 'multicast')):
                found_branch = True
                continue
            if found_branch:
                after_branch.append(child)

        # Render before-branch elements
        for elem in before_branch:
            elem_id = elem.get('id', '')
            elem_tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            detail = get_element_detail(elem, elem_tag, proc_map.get(elem_id, {}))
            box_class = get_box_class(elem_tag, elem)
            route_link = get_route_link_from_element(elem, elem_tag)

            box_parts, actual_height = draw_box(branch_x - box_width/2, current_y, box_width, box_height,
                                       elem_id, elem_tag, detail, box_class, route_link)
            svg_parts.extend(box_parts)
            current_y += actual_height + arrow_height
            svg_parts.append(f'<line x1="{branch_x}" y1="{current_y - arrow_height}" x2="{branch_x}" y2="{current_y}" class="arrow" />')

        # Render the branching element
        branch_id = branch_elem.get('id', branch_tag)
        branches = []

        if choice_elem is not None:
            # Extract choice branches
            when_elems = choice_elem.findall('.//camel:when', ns) or choice_elem.findall('.//when')
            otherwise_elem = choice_elem.find('.//camel:otherwise', ns) or choice_elem.find('.//otherwise')

            for i, when_elem in enumerate(when_elems):
                branches.append({'label': f'when #{i+1}', 'elements': list(when_elem)})

            if otherwise_elem is not None:
                branches.append({'label': 'otherwise', 'elements': list(otherwise_elem)})
        elif multicast_elem is not None:
            # Extract multicast branches
            to_elems = [elem for elem in multicast_elem if elem.tag.endswith('to')]
            for i, to_elem in enumerate(to_elems):
                uri = to_elem.get('uri', '')
                branches.append({'label': f'branch {i+1}: {uri}', 'elements': [to_elem], 'uri': uri})

        # Draw branching box
        branch_box_class = f"{branch_tag}-box"
        box_parts, actual_height = draw_box(branch_x - box_width/2, current_y, box_width, box_height,
                                   branch_id, branch_tag, f"{len(branches)} branches", branch_box_class)
        svg_parts.extend(box_parts)
        current_y += actual_height + arrow_height

        # Calculate branch positions
        num_branches = len(branches)
        branch_spacing = max(350, box_width + 100)
        total_branch_width = (num_branches - 1) * branch_spacing
        start_branch_x = branch_x - total_branch_width / 2

        # Draw each branch
        branch_end_positions = []
        for i, branch in enumerate(branches):
            sub_branch_x = start_branch_x + i * branch_spacing
            sub_branch_y = current_y

            # Draw arrow to branch
            svg_parts.append(f'<line x1="{branch_x}" y1="{current_y - arrow_height}" x2="{sub_branch_x}" y2="{sub_branch_y}" class="arrow" />')
            svg_parts.append(f'<text x="{sub_branch_x}" y="{sub_branch_y - 10}" text-anchor="middle" class="branch-label">{branch["label"]}</text>')

            # Draw branch elements
            for elem in branch['elements']:
                elem_id = elem.get('id', '')
                elem_tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                detail = get_element_detail(elem, elem_tag, proc_map.get(elem_id, {}))
                box_class = get_box_class(elem_tag, elem)
                route_link = get_route_link_from_element(elem, elem_tag)

                box_parts, actual_height = draw_box(sub_branch_x - box_width/2, sub_branch_y, box_width, box_height,
                                           elem_id, elem_tag, detail, box_class, route_link)
                svg_parts.extend(box_parts)
                sub_branch_y += actual_height
                # Only add arrow between elements
                if branch['elements'].index(elem) < len(branch['elements']) - 1:
                    sub_branch_y += arrow_height
                    svg_parts.append(f'<line x1="{sub_branch_x}" y1="{sub_branch_y - arrow_height}" x2="{sub_branch_x}" y2="{sub_branch_y}" class="arrow" />')

            branch_end_positions.append(sub_branch_y)

        # Find max branch end
        max_branch_end_y = max(branch_end_positions) if branch_end_positions else current_y
        current_y = max_branch_end_y

        # Draw merge arrows
        merge_point_y = current_y + arrow_height
        for i in range(num_branches):
            sub_branch_x = start_branch_x + i * branch_spacing
            svg_parts.append(f'<line x1="{sub_branch_x}" y1="{branch_end_positions[i]}" x2="{branch_x}" y2="{merge_point_y}" class="arrow" />')

        # Position next element at the merge point
        current_y = merge_point_y

        # Render after-branch elements
        for elem in after_branch:
            elem_id = elem.get('id', '')
            elem_tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            detail = get_element_detail(elem, elem_tag, proc_map.get(elem_id, {}))
            box_class = get_box_class(elem_tag, elem)
            route_link = get_route_link_from_element(elem, elem_tag)

            box_parts, actual_height = draw_box(branch_x - box_width/2, current_y, box_width, box_height,
                                       elem_id, elem_tag, detail, box_class, route_link)
            svg_parts.extend(box_parts)
            current_y += actual_height
            if after_branch.index(elem) < len(after_branch) - 1:
                current_y += arrow_height
                svg_parts.append(f'<line x1="{branch_x}" y1="{current_y - arrow_height}" x2="{branch_x}" y2="{current_y}" class="arrow" />')

        return svg_parts, current_y

    except Exception as e:
        logger.error(f"Error rendering inlined route with branching: {e}")
        return [], branch_y


def generate_sequential_route_svg(route_id, from_id, from_uri, processors, route_xml=None):
    """Generate SVG visualization for a sequential route with route inlining"""

    # SVG configuration
    box_width = 300
    box_height = 80
    start_x = 50
    start_y = 50
    arrow_height = 30

    # We'll collect all elements to draw, then calculate total height
    elements_to_draw = []

    # Add from box
    elements_to_draw.append({
        'type': 'from',
        'id': from_id,
        'detail': from_uri,
        'box_class': 'from-box'
    })

    # Parse route XML to get URIs for "to" processors
    to_uri_map = {}
    if route_xml:
        try:
            root = ET.fromstring(route_xml)
            for child in root:
                tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                if tag == 'to':
                    elem_id = child.get('id', '')
                    uri = child.get('uri', '')
                    if elem_id:
                        to_uri_map[elem_id] = uri
        except Exception as e:
            logger.error(f"Error parsing route XML for URIs: {e}")

    # Process each processor, expanding "to" calls inline
    for proc in processors:
        proc_type = proc.get('processorName', 'default')
        proc_id = proc.get('processorId', '')

        # Check if this is a "to" processor calling a direct route
        if proc_type == 'to' and proc_id in to_uri_map:
            uri = to_uri_map[proc_id]

            # Try to inline the called route
            if uri.startswith('direct:'):
                called_route_xml = fetch_route_by_uri(uri)
                if called_route_xml:
                    # Extract route ID from XML
                    route_root = ET.fromstring(called_route_xml)
                    called_route_id = route_root.get('id', uri.replace('direct:', '') + '-route')

                    # Add a grey indicator box showing we're calling another route
                    elements_to_draw.append({
                        'type': 'route-call',
                        'id': '',
                        'detail': f'Calling route: {called_route_id}',
                        'box_class': 'route-call-box',
                        'route_link': called_route_id
                    })

                    # Parse and inline the called route's processors
                    inlined_procs = parse_route_processors(called_route_xml)

                    for inlined_proc in inlined_procs:
                        tag = inlined_proc['tag']
                        elem = inlined_proc['element']

                        # Get details for this processor
                        detail = get_element_detail(elem, tag, {})
                        box_class = get_box_class(tag, elem)
                        route_link = get_route_link_from_element(elem, tag)

                        elements_to_draw.append({
                            'type': tag,
                            'id': elem.get('id', ''),
                            'detail': detail,
                            'box_class': box_class,
                            'route_link': route_link
                        })
                else:
                    # Couldn't fetch route, use fallback route name
                    fallback_route_name = uri.replace('direct:', '') + '-route'
                    elements_to_draw.append({
                        'type': 'to',
                        'id': proc_id,
                        'detail': uri,
                        'box_class': 'default-box',
                        'route_link': fallback_route_name
                    })
            else:
                # Non-direct URI, show as "to" box
                elements_to_draw.append({
                    'type': 'to',
                    'id': proc_id,
                    'detail': uri,
                    'box_class': 'default-box'
                })
        else:
            # Regular processor
            detail = ""
            if proc_type == "log":
                detail = proc.get('message', '')
            elif proc_type == "setBody":
                expr = proc.get('expression', '')
                lang = proc.get('expressionLanguage', '')
                detail = f"{lang}: {expr}"

            box_class = f"{proc_type.lower()}-box" if proc_type.lower() in ['log', 'setbody', 'choice'] else "default-box"

            elements_to_draw.append({
                'type': proc_type,
                'id': proc_id,
                'detail': detail,
                'box_class': box_class
            })

    # Calculate total height dynamically
    total_height = start_y * 2 + (len(elements_to_draw) * (box_height + arrow_height))
    svg_width = start_x * 2 + box_width

    # Start SVG
    svg_parts = [
        f'<svg width="{svg_width}" height="{total_height}" xmlns="http://www.w3.org/2000/svg">',
        '<defs>',
        '<style>',
        '.box { stroke: #333; stroke-width: 2; }',
        '.from-box { fill: #4CAF50; }',
        '.log-box { fill: #2196F3; }',
        '.setbody-box { fill: #FF9800; }',
        '.choice-box { fill: #9C27B0; }',
        '.default-box { fill: #9E9E9E; }',
        '.route-call-box { fill: #757575; }',
        '.box-text { fill: white; font-family: Arial, sans-serif; font-size: 14px; font-weight: bold; }',
        '.box-detail { fill: white; font-family: Arial, sans-serif; font-size: 11px; }',
        '.arrow { stroke: #333; stroke-width: 2; fill: none; marker-end: url(#arrowhead); }',
        '.branch-label { fill: #333; font-family: Arial, sans-serif; font-size: 12px; font-weight: bold; }',
        'a { cursor: pointer; }',
        'a:hover .route-call-box { fill: #555555; }',
        '</style>',
        '<marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">',
        '<polygon points="0 0, 10 3, 0 6" fill="#333" />',
        '</marker>',
        '</defs>',
        f'<text x="{svg_width/2}" y="25" text-anchor="middle" style="font-family: Arial; font-size: 18px; font-weight: bold; fill: #333;">Route: {route_id}</text>',
    ]

    current_y = start_y

    # Draw all elements
    for i, elem in enumerate(elements_to_draw):
        # Draw box
        box_parts, actual_height = draw_box(
            start_x, current_y, box_width, box_height,
            elem['id'], elem['type'], elem['detail'], elem['box_class'], elem.get('route_link')
        )
        svg_parts.extend(box_parts)
        current_y += actual_height

        # Draw arrow to next element (if not last)
        if i < len(elements_to_draw) - 1:
            arrow_x = start_x + box_width / 2
            svg_parts.append(
                f'<line x1="{arrow_x}" y1="{current_y}" x2="{arrow_x}" y2="{current_y + arrow_height}" class="arrow" />'
            )
            current_y += arrow_height

    svg_parts.append('</svg>')

    return '\n'.join(svg_parts)


def wrap_text(text, max_chars_per_line=35):
    """Wrap text into multiple lines"""
    if len(text) <= max_chars_per_line:
        return [text]

    words = text.split()
    lines = []
    current_line = []
    current_length = 0

    for word in words:
        word_length = len(word)
        # +1 for the space
        if current_length + word_length + (1 if current_line else 0) <= max_chars_per_line:
            current_line.append(word)
            current_length += word_length + (1 if len(current_line) > 1 else 0)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_length = word_length

    if current_line:
        lines.append(' '.join(current_line))

    return lines


def get_route_link_from_element(elem, elem_tag):
    """Extract actual route ID from a 'to' element with direct: URI for linking

    Returns: route ID (str) or None
    """
    if elem_tag.lower() == 'to':
        uri = elem.get('uri', '')
        if uri.startswith('direct:'):
            # Fetch the route XML to get the actual route ID
            route_xml = fetch_route_by_uri(uri)
            if route_xml:
                try:
                    route_root = ET.fromstring(route_xml)
                    route_id = route_root.get('id')
                    if route_id:
                        return route_id
                except Exception as e:
                    logger.warning(f"Failed to parse route XML for {uri}: {e}")
            # Fallback: append -route to the direct name
            return uri.replace('direct:', '') + '-route'
    return None


def draw_box(x, y, width, height, box_id, box_type, detail, box_class, route_link=None):
    """Draw a single box in the SVG - returns (svg_parts, actual_height)

    Args:
        route_link: If provided, wraps the box in an <a> tag linking to /route/{route_link}/graph
    """
    # Calculate how many lines the detail text will take
    actual_height = height
    if detail:
        lines = wrap_text(detail, max_chars_per_line=35)
        num_lines = len(lines)
        if num_lines > 1:
            # Add 7 pixels per extra line
            actual_height = height + (num_lines - 1) * 7

    # Customize box title for route-call boxes
    display_title = "→ Call Route" if box_type == "route-call" else box_type

    parts = []

    # Wrap in <a> tag if route_link is provided
    if route_link:
        parts.append(f'<a href="/route/{route_link}/graph">')

    parts.extend([
        f'<rect x="{x}" y="{y}" width="{width}" height="{actual_height}" class="box {box_class}" rx="5" />',
        f'<text x="{x + width/2}" y="{y + 25}" text-anchor="middle" class="box-text">{display_title}</text>',
        f'<text x="{x + width/2}" y="{y + 42}" text-anchor="middle" class="box-detail">ID: {box_id}</text>',
    ])

    # Add detail text if available with multiline support
    if detail:
        lines = wrap_text(detail, max_chars_per_line=35)

        # Start detail text at y + 60, with 13px line height for each additional line
        text_elem_parts = [f'<text x="{x + width/2}" y="{y + 60}" text-anchor="middle" class="box-detail">']

        for i, line in enumerate(lines):
            dy = "0em" if i == 0 else "1.2em"
            x_pos = x + width/2
            text_elem_parts.append(f'<tspan x="{x_pos}" dy="{dy}">{line}</tspan>')

        text_elem_parts.append('</text>')
        parts.append(''.join(text_elem_parts))

    # Close <a> tag if route_link was provided
    if route_link:
        parts.append('</a>')

    return parts, actual_height


if __name__ == '__main__':
    app.run(debug=True, port=5000)
