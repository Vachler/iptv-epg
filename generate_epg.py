import gzip
import urllib.request
import xml.etree.ElementTree as ET
from copy import deepcopy


SOURCES = [
    # Hlavní CZ/SK EPG
    "https://epg.m3u8.cz/xmltv.php?format=xml",

    # Další CZ/SK, filmové, dokumentární atd.
    "https://iptv-epg.org/files/epg-cz.xml.gz",

    # Britské sportovní stanice
    "https://raw.githubusercontent.com/farleyflex/epg-guide/main/epg.xml",
]

OUTPUT_XML = "epg.xml"
OUTPUT_GZ = "epg.xml.gz"


def download(url):
    print(f"Stahuji: {url}")

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 IPTV-EPG-Updater"},
    )

    with urllib.request.urlopen(request, timeout=180) as response:
        data = response.read()

    # Automaticky rozbalí .gz
    if data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)

    return ET.fromstring(data)


def main():
    output = ET.Element(
        "tv",
        {"generator-info-name": "Vachler IPTV EPG"},
    )

    channels = {}
    programmes = set()

    total_programmes = 0

    for url in SOURCES:
        try:
            root = download(url)

            print(
                f"  nalezeno {len(root.findall('channel'))} kanálů"
            )

            # ---------------------------
            # KANÁLY
            # ---------------------------

            for channel in root.findall("channel"):
                channel_id = channel.get("id")

                if not channel_id:
                    continue

                # První zdroj má přednost.
                if channel_id not in channels:
                    channels[channel_id] = deepcopy(channel)

            # ---------------------------
            # POŘADY
            # ---------------------------

            for programme in root.findall("programme"):
                channel_id = programme.get("channel")
                start = programme.get("start")
                stop = programme.get("stop")

                if not channel_id or not start:
                    continue

                # Zabrání přesným duplicitám.
                key = (
                    channel_id,
                    start,
                    stop,
                )

                if key in programmes:
                    continue

                programmes.add(key)
                output.append(deepcopy(programme))
                total_programmes += 1

        except Exception as error:
            print()
            print(f"VAROVÁNÍ: {url}")
            print(error)
            print()

    # Kanály musí být v XML před pořady.
    final = ET.Element(
        "tv",
        {"generator-info-name": "Vachler IPTV EPG"},
    )

    for channel in channels.values():
        final.append(channel)

    # Přesuneme všechny pořady za seznam kanálů.
    for programme in output.findall("programme"):
        final.append(programme)

    tree = ET.ElementTree(final)

    try:
        ET.indent(tree, space="  ")
    except AttributeError:
        pass

    tree.write(
        OUTPUT_XML,
        encoding="utf-8",
        xml_declaration=True,
    )

    with open(OUTPUT_XML, "rb") as source:
        with gzip.open(
            OUTPUT_GZ,
            "wb",
            compresslevel=9,
        ) as target:
            target.write(source.read())

    print()
    print("==============================")
    print("HOTOVO")
    print("==============================")
    print(f"Kanály: {len(channels)}")
    print(f"Pořady: {total_programmes}")
    print(f"Vytvořeno: {OUTPUT_XML}")
    print(f"Vytvořeno: {OUTPUT_GZ}")


if __name__ == "__main__":
    main()