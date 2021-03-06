#!/usr/bin/python3

import simplekml
import utm

from api import Descripciones, Organismo, Puesto, dict_from_txt

puestos = [p for p in Puesto.load() if p.idCentroDirectivo !=
           1301 and p.idProvision not in ("L",) and p.isTAI()]

descripciones = Descripciones.load()
organismos = Organismo.load()
rcp_organi = {}
for o in organismos:
    for c in o.codigos:
        if isinstance(c, int):
            rcp_organi[c] = o

kml = simplekml.Kml()
kml.document.name = "TAI"

style_normal = simplekml.Style()
style_normal.iconstyle.color = simplekml.Color.blue
style_normal.iconstyle.icon.href = 'http://maps.google.com/mapfiles/ms/micons/blue.png'

kml.document.style = style_normal

style_con_vacantes = simplekml.Style()
style_con_vacantes.iconstyle.color = simplekml.Color.green
style_con_vacantes.iconstyle.icon.href = 'http://maps.google.com/mapfiles/ms/micons/green.png'

kml.document.style = style_con_vacantes

style_sin_puestos = simplekml.Style()
style_sin_puestos.iconstyle.color = simplekml.Color.red
style_sin_puestos.iconstyle.icon.href = 'http://maps.google.com/mapfiles/ms/micons/red.png'

kml.document.style = style_sin_puestos

style_nivel_alto = simplekml.Style()
style_nivel_alto.iconstyle.color = simplekml.Color.blue
style_nivel_alto.iconstyle.icon.href = 'http://maps.google.com/mapfiles/ms/micons/grey.png'

kml.document.style = style_nivel_alto

style_sin_latlon = simplekml.Style()
style_sin_latlon.iconstyle.color = simplekml.Color.black
style_sin_latlon.iconstyle.icon.href = 'http://maps.google.com/mapfiles/ms/micons/question.png'

kml.document.style = style_sin_latlon

folderVerde = kml.newfolder(name="Con vacantes")
folderVerde.description = "Lugares en los que hay puestos vacantes según los RPT"

folderAzul = kml.newfolder(name="Sin vacantes")
folderAzul.description = "Lugares los que hay puestos TAI según los RPT pero ninguno vacante"

folderRojo = kml.newfolder(name="Añadidos porque sí")
folderRojo.description = "Lugares en los que no hay puestos TAI según RPT pero los añadimos por alguna otra consideración"

folderGris = kml.newfolder(name="Solo puestos TAI de nivel alto")
folderGris.description = "Lugares en los que hay puestos TAI (vacantes o no) según RPT pero solo de niveles por encima de lo usual (>18)"

folderInte = kml.newfolder(name="Organismos sin dirección exacta")
folderInte.description = "Solo sabemos la provincia o una dirección que no tiene coordenadas, así que lo centramos en la provincia en cuestión y punto"

for p in puestos:
    unidad = rcp_organi.get(p.idUnidad, None)
    minist = rcp_organi.get(p.idMinisterio, None)
    centro = rcp_organi.get(p.idCentroDirectivo, None)
    padreUnidad = centro or minist
    if unidad:
        if unidad.latlon:
            unidad.puestos.add(p)
            continue
        if padreUnidad and unidad.idProvincia is not None and unidad.idProvincia != padreUnidad.idProvincia:
            unidad.puestos.add(p)
            continue
    if centro:
        if centro.latlon:
            centro.puestos.add(p)
            continue
        if centro.idProvincia is not None and centro.idProvincia != minist.idProvincia:
            centro.puestos.add(p)
            continue
    if minist:
        if minist.latlon or minist.idProvincia:
            minist.puestos.add(p)
            continue

cod_dir_latlon = dict_from_txt("arreglos/dir_latlon.txt", rever=True)
provin_org = {}
for o in organismos:
    if not o.latlon and o.idProvincia is not None and (o.puestos or o.nombre == "area de informatica"):
        latlon = cod_dir_latlon.get(o.idProvincia)
        col = provin_org.get(latlon, set())
        col.add(o)
        provin_org[latlon] = col

latlon_org = {}
for o in organismos:
    if o.latlon and (o.puestos or o.nombre == "area de informatica"):
        col = latlon_org.get(o.latlon, set())
        col.add(o)
        latlon_org[o.latlon] = col


def count_puestos(*args):
    vacantes = 0
    normales = 0
    grannivel = 0
    for p in args:
        if p.nivel > 18:
            grannivel += 1
        elif p.estado == "V":
            vacantes += 1
        else:
            normales += 1
    return normales, vacantes, grannivel


def crear_descripcion(orgs):
    count = len(orgs)
    if count == 1:
        org = next(iter(orgs))
        name = "%s (%s)" % (org.deOrganismo, org.idOrganismo)
    else:
        name = str(count) + " organismos"

    description = ""
    direcciones = set([o.deDireccion for o in orgs])
    if len(direcciones) == 1:
        deDireccion = next(iter(orgs)).deDireccion
        if deDireccion:
            description += deDireccion + "\n\n"
    org_puestos = set()
    for org in orgs:
        if count > 1:
            description += "%s - %s\n" % (org.idOrganismo, org.deOrganismo)
        if len(direcciones) > 1 and org.deDireccion:
            description += "Dirección: %s\n" % (org.deDireccion,)
        if org.url:
            description += org.url
        dePuestos = sorted(set([p.abbr_puesto for p in org.puestos]))
        for dePuesto in dePuestos:
            puestos = [p for p in org.puestos if p.abbr_puesto == dePuesto]
            if len(puestos) == 1:
                p = puestos[0]
                description += "\n%s/%s - %s" % (p.idPuesto,
                                                 p.nivel, p.abbr_puesto)
            else:
                description += "\n(%s) %s:" % (len(puestos), dePuesto)
                for p in sorted(puestos, key=lambda p: p.idPuesto):
                    description += " %s/%s," % (p.idPuesto, p.nivel)
                description = description[:-1] + "\n"
        org_puestos = org_puestos.union(org.puestos)
        description += "\n\n"

    description = description.strip()
    description = description.replace("\n", "<br/>\n")
    return name, description, org_puestos


print ("Se van a crear %s puntos inexactos" % len(provin_org))
for latlon, orgs in provin_org.items():
    name, descripcion, _ = crear_descripcion(orgs)
    utm_split = latlon.split(",")
    latlon = (float(utm_split[1]), float(utm_split[0]))

    pnt = folderInte.newpoint(name=name, coords=[latlon])
    pnt.style = style_sin_latlon

    pnt.description = descripcion

print ("Se van a crear %s puntos exactos" % len(latlon_org))
for latlon, orgs in latlon_org.items():
    name, descripcion, org_puestos = crear_descripcion(orgs)
    utm_split = latlon.split(",")
    latlon = (float(utm_split[1]), float(utm_split[0]))

    if len(org_puestos) == 0:
        pnt = folderRojo.newpoint(name=name, coords=[latlon])
        pnt.style = style_sin_puestos
    else:
        normales, vacantes, grannivel = count_puestos(*org_puestos)
        if grannivel == len(org_puestos):
            pnt = folderGris.newpoint(name=name, coords=[latlon])
            pnt.style = style_nivel_alto
        elif vacantes > 0:
            pnt = folderVerde.newpoint(name=name, coords=[latlon])
            pnt.style = style_con_vacantes
        else:
            pnt = folderAzul.newpoint(name=name, coords=[latlon])

    pnt.description = descripcion

kml.save("docs/mapa/tai.kml")
