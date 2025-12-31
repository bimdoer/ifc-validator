"""Vergleicht zwei IFC-Dateien und zeigt Unterschiede auf."""

import sys
import os
from pathlib import Path
import ifcopenshell
from typing import Dict, Any, List, Set

def analyze_ifc_file(file_path: str) -> Dict[str, Any]:
    """Analysiert eine IFC-Datei und gibt Metadaten zurück."""
    path = Path(file_path)
    
    # Basis-Informationen
    info = {
        'file_path': str(path),
        'file_name': path.name,
        'file_size': path.stat().st_size if path.exists() else 0,
        'exists': path.exists(),
        'loadable': False,
        'error': None,
        'ifc_file': None,
    }
    
    if not path.exists():
        info['error'] = "Datei existiert nicht"
        return info
    
    # Versuche Datei zu laden
    try:
        ifc_file = ifcopenshell.open(str(path))
        info['loadable'] = True
        info['ifc_file'] = ifc_file
    except Exception as e:
        info['error'] = str(e)
        return info
    
    # IFC-Version und Schema
    try:
        info['schema'] = ifc_file.schema
        info['version'] = ifc_file.wrapped_data.header.file_description.description[0] if hasattr(ifc_file.wrapped_data, 'header') else 'Unknown'
    except Exception as e:
        info['schema_error'] = str(e)
    
    # Anzahl verschiedener IFC-Typen
    try:
        type_counts = {}
        for entity in ifc_file.by_type('IfcRoot'):
            entity_type = entity.is_a()
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
        info['type_counts'] = type_counts
        info['total_entities'] = len(ifc_file.by_type('IfcRoot'))
    except Exception as e:
        info['type_counts_error'] = str(e)
    
    # Projekt-Informationen
    try:
        projects = ifc_file.by_type('IfcProject')
        if projects:
            project = projects[0]
            info['project'] = {
                'global_id': project.GlobalId if hasattr(project, 'GlobalId') else None,
                'name': project.Name if hasattr(project, 'Name') else None,
            }
        else:
            info['project'] = None
    except Exception as e:
        info['project_error'] = str(e)
    
    # Sites
    try:
        sites = ifc_file.by_type('IfcSite')
        info['sites_count'] = len(sites)
        if sites:
            info['sites'] = [{
                'global_id': s.GlobalId if hasattr(s, 'GlobalId') else None,
                'name': s.Name if hasattr(s, 'Name') else None,
            } for s in sites]
    except Exception as e:
        info['sites_error'] = str(e)
    
    # Buildings
    try:
        buildings = ifc_file.by_type('IfcBuilding')
        info['buildings_count'] = len(buildings)
    except Exception as e:
        info['buildings_error'] = str(e)
    
    # Building Storeys
    try:
        storeys = ifc_file.by_type('IfcBuildingStorey')
        info['storeys_count'] = len(storeys)
        if storeys:
            info['storeys'] = [{
                'global_id': s.GlobalId if hasattr(s, 'GlobalId') else None,
                'name': s.Name if hasattr(s, 'Name') else None,
                'elevation': s.Elevation if hasattr(s, 'Elevation') else None,
            } for s in storeys]
    except Exception as e:
        info['storeys_error'] = str(e)
    
    # Wände
    try:
        walls = ifc_file.by_type('IfcWall')
        info['walls_count'] = len(walls)
    except Exception as e:
        info['walls_error'] = str(e)
    
    # Türen
    try:
        doors = ifc_file.by_type('IfcDoor')
        info['doors_count'] = len(doors)
    except Exception as e:
        info['doors_error'] = str(e)
    
    # Fenster
    try:
        windows = ifc_file.by_type('IfcWindow')
        info['windows_count'] = len(windows)
    except Exception as e:
        info['windows_error'] = str(e)
    
    # Räumliche Relationen
    try:
        contained_relations = ifc_file.by_type('IfcRelContainedInSpatialStructure')
        info['contained_relations_count'] = len(contained_relations)
    except Exception as e:
        info['contained_relations_error'] = str(e)
    
    # Decomposition Relationen
    try:
        decomposed_relations = ifc_file.by_type('IfcRelDecomposes')
        info['decomposed_relations_count'] = len(decomposed_relations)
    except Exception as e:
        info['decomposed_relations_error'] = str(e)
    
    # Header-Informationen (erste Zeilen der Datei)
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            first_lines = [f.readline().strip() for _ in range(10)]
            info['file_header'] = first_lines
    except Exception as e:
        info['header_read_error'] = str(e)
    
    # Mesh- und Geometrie-Analyse
    if info['loadable'] and info['ifc_file']:
        try:
            mesh_info = analyze_meshes(info['ifc_file'])
            info['mesh_info'] = mesh_info
        except Exception as e:
            info['mesh_analysis_error'] = str(e)
            import traceback
            info['mesh_analysis_traceback'] = traceback.format_exc()
    
    return info


def analyze_meshes(ifc_file) -> Dict[str, Any]:
    """Analysiert Meshes und Geometrien in einer IFC-Datei."""
    mesh_info = {
        'total_products_with_geometry': 0,
        'total_products_without_geometry': 0,
        'geometry_errors': [],
        'representation_types': {},
        'representation_identifiers': {},
        'item_types': {},
        'products_without_geometry_details': [],
        'mesh_by_type': {},
        'invalid_geometries': [],
        'geometry_statistics': {
            'total_representations': 0,
            'total_items': 0,
            'products_with_multiple_representations': 0,
        }
    }
    
    try:
        # Alle Produkte durchgehen
        products = ifc_file.by_type('IfcProduct')
        
        for product in products:
            product_type = product.is_a()
            
            # Zähle nach Typ
            if product_type not in mesh_info['mesh_by_type']:
                mesh_info['mesh_by_type'][product_type] = {
                    'total': 0,
                    'with_geometry': 0,
                    'without_geometry': 0,
                    'errors': 0,
                    'representation_identifiers': {},
                    'item_types': {}
                }
            mesh_info['mesh_by_type'][product_type]['total'] += 1
            
            # Prüfe ob Produkt Geometrie hat
            has_geometry = False
            geometry_error = None
            representation_count = 0
            
            try:
                # Versuche Representation zu bekommen
                if hasattr(product, 'Representation') and product.Representation:
                    representation_count = len(product.Representation.Representations) if hasattr(product.Representation, 'Representations') else 1
                    if representation_count > 1:
                        mesh_info['geometry_statistics']['products_with_multiple_representations'] += 1
                    
                    # Gehe durch alle Representations
                    representations = product.Representation.Representations if hasattr(product.Representation, 'Representations') else [product.Representation]
                    
                    for representation in representations:
                        if representation:
                            has_geometry = True
                            mesh_info['geometry_statistics']['total_representations'] += 1
                            
                            # Representation Identifier (z.B. "Body", "Axis", "FootPrint")
                            rep_identifier = None
                            if hasattr(representation, 'RepresentationIdentifier'):
                                rep_id = representation.RepresentationIdentifier
                                if rep_id:
                                    rep_identifier = str(rep_id)
                                    mesh_info['representation_identifiers'][rep_identifier] = \
                                        mesh_info['representation_identifiers'].get(rep_identifier, 0) + 1
                                    mesh_info['mesh_by_type'][product_type]['representation_identifiers'][rep_identifier] = \
                                        mesh_info['mesh_by_type'][product_type]['representation_identifiers'].get(rep_identifier, 0) + 1
                            
                            # Representation Type (z.B. "IfcShapeRepresentation")
                            if hasattr(representation, 'is_a'):
                                rep_type = representation.is_a()
                                mesh_info['representation_types'][rep_type] = \
                                    mesh_info['representation_types'].get(rep_type, 0) + 1
                            
                            # Items in Representation
                            if hasattr(representation, 'Items') and representation.Items:
                                for item in representation.Items:
                                    mesh_info['geometry_statistics']['total_items'] += 1
                                    
                                    # Item Type (z.B. "IfcExtrudedAreaSolid", "IfcFacetedBrep")
                                    item_type = item.is_a()
                                    mesh_info['item_types'][item_type] = \
                                        mesh_info['item_types'].get(item_type, 0) + 1
                                    mesh_info['mesh_by_type'][product_type]['item_types'][item_type] = \
                                        mesh_info['mesh_by_type'][product_type]['item_types'].get(item_type, 0) + 1
                                    
                                    # Prüfe auf bekannte Probleme
                                    try:
                                        # Versuche auf Geometrie zuzugreifen
                                        if hasattr(item, 'StyledByItem'):
                                            pass  # OK
                                        if hasattr(item, 'LayerAssignments'):
                                            pass  # OK
                                        
                                        # Prüfe spezielle Item-Typen, die web-ifc möglicherweise nicht unterstützt
                                        if item_type in ['IfcBooleanResult', 'IfcBooleanClippingResult']:
                                            # Diese können problematisch sein
                                            pass
                                            
                                    except Exception as item_error:
                                        geometry_error = f"Item error ({item_type}): {str(item_error)}"
                else:
                    has_geometry = False
                    # Speichere Details über Produkte ohne Geometrie
                    if len(mesh_info['products_without_geometry_details']) < 20:
                        mesh_info['products_without_geometry_details'].append({
                            'type': product_type,
                            'global_id': product.GlobalId if hasattr(product, 'GlobalId') else None,
                            'name': product.Name if hasattr(product, 'Name') else None,
                            'has_representation_attr': hasattr(product, 'Representation'),
                            'representation_value': str(product.Representation) if hasattr(product, 'Representation') else None
                        })
                
                if has_geometry:
                    mesh_info['total_products_with_geometry'] += 1
                    mesh_info['mesh_by_type'][product_type]['with_geometry'] += 1
                else:
                    mesh_info['total_products_without_geometry'] += 1
                    mesh_info['mesh_by_type'][product_type]['without_geometry'] += 1
                    
            except Exception as e:
                geometry_error = str(e)
                mesh_info['total_products_without_geometry'] += 1
                mesh_info['mesh_by_type'][product_type]['without_geometry'] += 1
                mesh_info['mesh_by_type'][product_type]['errors'] += 1
            
            if geometry_error:
                mesh_info['geometry_errors'].append({
                    'product_type': product_type,
                    'product_id': product.id() if hasattr(product, 'id') else None,
                    'global_id': product.GlobalId if hasattr(product, 'GlobalId') else None,
                    'error': geometry_error
                })
                
                if len(mesh_info['geometry_errors']) <= 10:  # Nur erste 10 speichern
                    mesh_info['invalid_geometries'].append({
                        'type': product_type,
                        'id': product.id() if hasattr(product, 'id') else None,
                    })
    
    except Exception as e:
        mesh_info['analysis_error'] = str(e)
        import traceback
        mesh_info['analysis_traceback'] = traceback.format_exc()
    
    return mesh_info


def compare_files(info1: Dict[str, Any], info2: Dict[str, Any]) -> None:
    """Vergleicht zwei IFC-Analysen und zeigt Unterschiede."""
    
    print("=" * 80)
    print("IFC-DATEIEN VERGLEICH")
    print("=" * 80)
    print()
    
    # Datei-Informationen
    print("📁 DATEI-INFORMATIONEN")
    print(f"\nDatei 1: {info1['file_name']}")
    print(f"  Pfad: {info1['file_path']}")
    print(f"  Größe: {info1['file_size']:,} Bytes ({info1['file_size'] / 1024 / 1024:.2f} MB)")
    print(f"  Existiert: {'✓' if info1['exists'] else '✗'}")
    print(f"  Ladebar: {'✓' if info1['loadable'] else '✗'}")
    if info1['error']:
        print(f"  ❌ Fehler: {info1['error']}")
    
    print(f"\nDatei 2: {info2['file_name']}")
    print(f"  Pfad: {info2['file_path']}")
    print(f"  Größe: {info2['file_size']:,} Bytes ({info2['file_size'] / 1024 / 1024:.2f} MB)")
    print(f"  Existiert: {'✓' if info2['exists'] else '✗'}")
    print(f"  Ladebar: {'✓' if info2['loadable'] else '✗'}")
    if info2['error']:
        print(f"  ❌ Fehler: {info2['error']}")
    
    if not info1['loadable'] or not info2['loadable']:
        print("\n⚠️ Eine oder beide Dateien konnten nicht geladen werden!")
        return
    
    print("\n" + "=" * 80)
    print("VERGLEICH DER IFC-INHALTE")
    print("=" * 80)
    
    # Schema
    print("\n📋 SCHEMA & VERSION")
    schema1 = info1.get('schema', 'Unknown')
    schema2 = info2.get('schema', 'Unknown')
    print(f"  Datei 1: {schema1}")
    print(f"  Datei 2: {schema2}")
    if schema1 != schema2:
        print(f"  ⚠️ Unterschied: {schema1} vs {schema2}")
    
    # Projekt
    print("\n🏗️ PROJEKT")
    proj1 = info1.get('project')
    proj2 = info2.get('project')
    if proj1:
        print(f"  Datei 1: {proj1.get('name', 'N/A')} (ID: {proj1.get('global_id', 'N/A')})")
    else:
        print("  Datei 1: Kein Projekt gefunden")
    if proj2:
        print(f"  Datei 2: {proj2.get('name', 'N/A')} (ID: {proj2.get('global_id', 'N/A')})")
    else:
        print("  Datei 2: Kein Projekt gefunden")
    
    # Strukturelle Elemente
    print("\n🏛️ STRUKTURELLE ELEMENTE")
    comparisons = [
        ('Sites', 'sites_count'),
        ('Buildings', 'buildings_count'),
        ('Storeys', 'storeys_count'),
        ('Walls', 'walls_count'),
        ('Doors', 'doors_count'),
        ('Windows', 'windows_count'),
    ]
    
    for label, key in comparisons:
        val1 = info1.get(key, 0)
        val2 = info2.get(key, 0)
        diff = val1 - val2
        marker = "⚠️" if diff != 0 else "✓"
        print(f"  {marker} {label}: Datei 1 = {val1}, Datei 2 = {val2} (Diff: {diff:+d})")
    
    # Relationen
    print("\n🔗 RELATIONEN")
    rel_comparisons = [
        ('ContainedInSpatialStructure', 'contained_relations_count'),
        ('RelDecomposes', 'decomposed_relations_count'),
    ]
    
    for label, key in rel_comparisons:
        val1 = info1.get(key, 0)
        val2 = info2.get(key, 0)
        diff = val1 - val2
        marker = "⚠️" if diff != 0 else "✓"
        print(f"  {marker} {label}: Datei 1 = {val1}, Datei 2 = {val2} (Diff: {diff:+d})")
    
    # IFC-Typen
    print("\n📊 IFC-TYPEN")
    types1 = set(info1.get('type_counts', {}).keys())
    types2 = set(info2.get('type_counts', {}).keys())
    
    only_in_1 = types1 - types2
    only_in_2 = types2 - types1
    common = types1 & types2
    
    print(f"  Gemeinsame Typen: {len(common)}")
    print(f"  Nur in Datei 1: {len(only_in_1)}")
    if only_in_1:
        print(f"    {', '.join(sorted(list(only_in_1))[:10])}{'...' if len(only_in_1) > 10 else ''}")
    print(f"  Nur in Datei 2: {len(only_in_2)}")
    if only_in_2:
        print(f"    {', '.join(sorted(list(only_in_2))[:10])}{'...' if len(only_in_2) > 10 else ''}")
    
    # Datei-Header
    print("\n📄 DATEI-HEADER (erste 5 Zeilen)")
    header1 = info1.get('file_header', [])[:5]
    header2 = info2.get('file_header', [])[:5]
    
    print("  Datei 1:")
    for i, line in enumerate(header1, 1):
        print(f"    {i}: {line[:80]}")
    
    print("  Datei 2:")
    for i, line in enumerate(header2, 1):
        print(f"    {i}: {line[:80]}")
    
    # Mesh- und Geometrie-Analyse
    print("\n" + "=" * 80)
    print("🔷 MESH- & GEOMETRIE-ANALYSE")
    print("=" * 80)
    
    mesh1 = info1.get('mesh_info', {})
    mesh2 = info2.get('mesh_info', {})
    
    if 'analysis_error' in mesh1:
        print("\n❌ Fehler bei Mesh-Analyse Datei 1:", mesh1.get('analysis_error', 'Unknown'))
    if 'analysis_error' in mesh2:
        print("\n❌ Fehler bei Mesh-Analyse Datei 2:", mesh2.get('analysis_error', 'Unknown'))
    
    if mesh1 and mesh2:
        # Produkte mit/ohne Geometrie
        print("\n📊 PRODUKTE MIT GEOMETRIE")
        with_geom1 = mesh1.get('total_products_with_geometry', 0)
        with_geom2 = mesh2.get('total_products_with_geometry', 0)
        without_geom1 = mesh1.get('total_products_without_geometry', 0)
        without_geom2 = mesh2.get('total_products_without_geometry', 0)
        
        print(f"  Datei 1: {with_geom1} mit Geometrie, {without_geom1} ohne Geometrie")
        print(f"  Datei 2: {with_geom2} mit Geometrie, {without_geom2} ohne Geometrie")
        
        diff_with = with_geom1 - with_geom2
        diff_without = without_geom1 - without_geom2
        if diff_with != 0 or diff_without != 0:
            print(f"  ⚠️ Unterschied: +{diff_with} mit Geometrie, +{diff_without} ohne Geometrie")
        
        # Geometrie-Fehler
        errors1 = len(mesh1.get('geometry_errors', []))
        errors2 = len(mesh2.get('geometry_errors', []))
        print(f"\n❌ GEOMETRIE-FEHLER")
        print(f"  Datei 1: {errors1} Fehler")
        print(f"  Datei 2: {errors2} Fehler")
        
        if errors1 > 0:
            print(f"\n  Erste Fehler in Datei 1:")
            for i, error in enumerate(mesh1.get('geometry_errors', [])[:5], 1):
                print(f"    {i}. {error.get('product_type', 'Unknown')}: {error.get('error', 'Unknown error')}")
        
        if errors2 > 0:
            print(f"\n  Erste Fehler in Datei 2:")
            for i, error in enumerate(mesh2.get('geometry_errors', [])[:5], 1):
                print(f"    {i}. {error.get('product_type', 'Unknown')}: {error.get('error', 'Unknown error')}")
        
        # Representation Types (Klassen wie IfcShapeRepresentation)
        print(f"\n📐 REPRESENTATION TYPES (Klassen)")
        rep_types1 = mesh1.get('representation_types', {})
        rep_types2 = mesh2.get('representation_types', {})
        
        all_rep_types = set(rep_types1.keys()) | set(rep_types2.keys())
        if all_rep_types:
            for rep_type in sorted(all_rep_types):
                count1 = rep_types1.get(rep_type, 0)
                count2 = rep_types2.get(rep_type, 0)
                diff = count1 - count2
                marker = "⚠️" if diff != 0 else "✓"
                print(f"  {marker} {rep_type}: Datei 1 = {count1}, Datei 2 = {count2} (Diff: {diff:+d})")
        
        # Representation Identifiers (Body, Axis, FootPrint, etc.)
        print(f"\n🏷️ REPRESENTATION IDENTIFIERS (Body, Axis, etc.)")
        rep_ids1 = mesh1.get('representation_identifiers', {})
        rep_ids2 = mesh2.get('representation_identifiers', {})
        
        all_rep_ids = set(rep_ids1.keys()) | set(rep_ids2.keys())
        if all_rep_ids:
            for rep_id in sorted(all_rep_ids):
                count1 = rep_ids1.get(rep_id, 0)
                count2 = rep_ids2.get(rep_id, 0)
                diff = count1 - count2
                marker = "⚠️" if diff != 0 else "✓"
                print(f"  {marker} {rep_id}: Datei 1 = {count1}, Datei 2 = {count2} (Diff: {diff:+d})")
        else:
            print("  (Keine Representation Identifiers gefunden)")
        
        # Item Types (Geometrie-Items wie IfcExtrudedAreaSolid, IfcFacetedBrep)
        print(f"\n🔷 GEOMETRIE ITEM TYPES")
        item_types1 = mesh1.get('item_types', {})
        item_types2 = mesh2.get('item_types', {})
        
        all_item_types = set(item_types1.keys()) | set(item_types2.keys())
        if all_item_types:
            # Sortiere nach Häufigkeit in Datei 1
            sorted_items = sorted(all_item_types, key=lambda x: item_types1.get(x, 0), reverse=True)
            for item_type in sorted_items[:15]:  # Top 15
                count1 = item_types1.get(item_type, 0)
                count2 = item_types2.get(item_type, 0)
                diff = count1 - count2
                marker = "⚠️" if diff != 0 else "✓"
                print(f"  {marker} {item_type}: Datei 1 = {count1}, Datei 2 = {count2} (Diff: {diff:+d})")
            
            if len(all_item_types) > 15:
                print(f"  ... und {len(all_item_types) - 15} weitere Item Types")
        else:
            print("  (Keine Item Types gefunden)")
        
        # Produkte ohne Geometrie - Details
        print(f"\n❓ PRODUKTE OHNE GEOMETRIE (Details)")
        without_geom_details1 = mesh1.get('products_without_geometry_details', [])
        without_geom_details2 = mesh2.get('products_without_geometry_details', [])
        
        if without_geom_details1:
            print(f"\n  Datei 1 - Erste {len(without_geom_details1)} Beispiele:")
            for i, detail in enumerate(without_geom_details1[:10], 1):
                name = detail.get('name', 'N/A') or 'N/A'
                gid = detail.get('global_id', 'N/A') or 'N/A'
                print(f"    {i}. {detail.get('type', 'Unknown')} - Name: {name[:40]}, ID: {gid[:20]}")
                if detail.get('has_representation_attr'):
                    print(f"       → Hat Representation-Attribut, aber Wert: {detail.get('representation_value', 'None')}")
        
        if without_geom_details2:
            print(f"\n  Datei 2 - Erste {len(without_geom_details2)} Beispiele:")
            for i, detail in enumerate(without_geom_details2[:10], 1):
                name = detail.get('name', 'N/A') or 'N/A'
                gid = detail.get('global_id', 'N/A') or 'N/A'
                print(f"    {i}. {detail.get('type', 'Unknown')} - Name: {name[:40]}, ID: {gid[:20]}")
                if detail.get('has_representation_attr'):
                    print(f"       → Hat Representation-Attribut, aber Wert: {detail.get('representation_value', 'None')}")
        
        # Mesh-Statistiken nach Typ
        print(f"\n🏗️ MESH-STATISTIKEN NACH TYP")
        mesh_by_type1 = mesh1.get('mesh_by_type', {})
        mesh_by_type2 = mesh2.get('mesh_by_type', {})
        
        all_types = set(mesh_by_type1.keys()) | set(mesh_by_type2.keys())
        important_types = ['IfcWall', 'IfcDoor', 'IfcWindow', 'IfcSlab', 'IfcColumn', 'IfcBeam', 'IfcRoof']
        
        for prod_type in important_types:
            if prod_type in all_types:
                stats1 = mesh_by_type1.get(prod_type, {})
                stats2 = mesh_by_type2.get(prod_type, {})
                
                total1 = stats1.get('total', 0)
                total2 = stats2.get('total', 0)
                with_geom1 = stats1.get('with_geometry', 0)
                with_geom2 = stats2.get('with_geometry', 0)
                without_geom1 = stats1.get('without_geometry', 0)
                without_geom2 = stats2.get('without_geometry', 0)
                errors1 = stats1.get('errors', 0)
                errors2 = stats2.get('errors', 0)
                
                if total1 > 0 or total2 > 0:
                    print(f"\n  {prod_type}:")
                    print(f"    Datei 1: {total1} total, {with_geom1} mit Geometrie, {without_geom1} ohne Geometrie, {errors1} Fehler")
                    print(f"    Datei 2: {total2} total, {with_geom2} mit Geometrie, {without_geom2} ohne Geometrie, {errors2} Fehler")
                    
                    # Zeige Representation Identifiers für diesen Typ
                    rep_ids1 = stats1.get('representation_identifiers', {})
                    rep_ids2 = stats2.get('representation_identifiers', {})
                    if rep_ids1 or rep_ids2:
                        all_rep_ids = set(rep_ids1.keys()) | set(rep_ids2.keys())
                        if all_rep_ids:
                            print(f"    Representation IDs: ", end="")
                            for rid in sorted(all_rep_ids):
                                c1 = rep_ids1.get(rid, 0)
                                c2 = rep_ids2.get(rid, 0)
                                print(f"{rid}({c1}/{c2}) ", end="")
                            print()
                    
                    # Zeige Item Types für diesen Typ
                    item_types1 = stats1.get('item_types', {})
                    item_types2 = stats2.get('item_types', {})
                    if item_types1 or item_types2:
                        all_item_types = set(item_types1.keys()) | set(item_types2.keys())
                        if all_item_types:
                            # Top 3 Item Types
                            sorted_items = sorted(all_item_types, key=lambda x: item_types1.get(x, 0) + item_types2.get(x, 0), reverse=True)
                            print(f"    Top Item Types: ", end="")
                            for it in sorted_items[:3]:
                                c1 = item_types1.get(it, 0)
                                c2 = item_types2.get(it, 0)
                                print(f"{it}({c1}/{c2}) ", end="")
                            print()
                    
                    if errors1 > 0 or errors2 > 0:
                        print(f"    ⚠️ Geometrie-Fehler gefunden!")
                    
                    if without_geom1 > 0 or without_geom2 > 0:
                        print(f"    ⚠️ {without_geom1 if without_geom1 > 0 else without_geom2} Produkte ohne Geometrie!")
    
    # Kritische Unterschiede
    print("\n" + "=" * 80)
    print("🔍 KRITISCHE UNTERSCHIEDE")
    print("=" * 80)
    
    critical_diffs = []
    
    if info1.get('contained_relations_count', 0) == 0 and info2.get('contained_relations_count', 0) > 0:
        critical_diffs.append("⚠️ Datei 1 hat keine IfcRelContainedInSpatialStructure Relationen!")
    
    if info1.get('contained_relations_count', 0) > 0 and info2.get('contained_relations_count', 0) == 0:
        critical_diffs.append("⚠️ Datei 2 hat keine IfcRelContainedInSpatialStructure Relationen!")
    
    if info1.get('storeys_count', 0) == 0 and info2.get('storeys_count', 0) > 0:
        critical_diffs.append("⚠️ Datei 1 hat keine IfcBuildingStorey Elemente!")
    
    if info1.get('storeys_count', 0) > 0 and info2.get('storeys_count', 0) == 0:
        critical_diffs.append("⚠️ Datei 2 hat keine IfcBuildingStorey Elemente!")
    
    if schema1 != schema2:
        critical_diffs.append(f"⚠️ Unterschiedliche IFC-Schemas: {schema1} vs {schema2}")
    
    # Mesh-bezogene kritische Unterschiede
    if mesh1 and mesh2:
        errors1 = len(mesh1.get('geometry_errors', []))
        errors2 = len(mesh2.get('geometry_errors', []))
        
        if errors1 > errors2 * 2:  # Mehr als doppelt so viele Fehler
            critical_diffs.append(f"⚠️ Datei 1 hat deutlich mehr Geometrie-Fehler ({errors1} vs {errors2})!")
        
        if errors2 > errors1 * 2:
            critical_diffs.append(f"⚠️ Datei 2 hat deutlich mehr Geometrie-Fehler ({errors2} vs {errors1})!")
        
        with_geom1 = mesh1.get('total_products_with_geometry', 0)
        with_geom2 = mesh2.get('total_products_with_geometry', 0)
        
        if with_geom1 == 0 and with_geom2 > 0:
            critical_diffs.append("⚠️ Datei 1 hat keine Produkte mit Geometrie!")
        
        if with_geom2 == 0 and with_geom1 > 0:
            critical_diffs.append("⚠️ Datei 2 hat keine Produkte mit Geometrie!")
    
    if critical_diffs:
        for diff in critical_diffs:
            print(f"  {diff}")
    else:
        print("  ✓ Keine kritischen strukturellen Unterschiede gefunden")
    
    print("\n" + "=" * 80)


def main():
    # Pfade zu den IFC-Dateien im Download-Ordner
    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
    
    file1_path = os.path.join(downloads_path, "P-172_ARC_REF_ALL_Allgemein_IFC2x3.ifc")
    file2_path = os.path.join(downloads_path, "Vectorworks2016-IFC2x3-EQUA_IDA_ICE.ifc")
    
    # Prüfe ob Dateien existieren
    if not os.path.exists(file1_path):
        print(f"❌ Datei 1 nicht gefunden: {file1_path}")
        print(f"   Bitte prüfen Sie den Dateinamen und Pfad.")
        sys.exit(1)
    
    if not os.path.exists(file2_path):
        print(f"❌ Datei 2 nicht gefunden: {file2_path}")
        print(f"   Bitte prüfen Sie den Dateinamen und Pfad.")
        sys.exit(1)
    
    print(f"📁 Datei 1: {file1_path}")
    print(f"📁 Datei 2: {file2_path}")
    print()
    
    print("Analysiere Datei 1...")
    info1 = analyze_ifc_file(file1_path)
    
    print("Analysiere Datei 2...")
    info2 = analyze_ifc_file(file2_path)
    
    compare_files(info1, info2)


if __name__ == "__main__":
    main()
