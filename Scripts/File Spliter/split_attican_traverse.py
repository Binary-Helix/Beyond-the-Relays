"""
split_attican_traverse.py

Splits a large solar_system_initializers file into the organized folder/file
structure, one .txt file per cluster per sector.

Sector folders:  btr_sector_<id>/   (e.g. btr_sector_at9, btr_sector_ic1, btr_sector_oc2)
Cluster files:   btr_<cluster_name>.txt

Sector header format expected in source file:
    ##### <Name> Sector - <ID> #####   (e.g. "Attican Traverse Sector - AT9")

Cluster header format expected in source file:
    ### <CLUSTER NAME> ###             (e.g. "### HADES NEXUS ###")

Usage (run from mod root):
    python3 Claude-Scripts/split_attican_traverse.py <source_file> <base_dir>

Examples:
    python3 Claude-Scripts/split_attican_traverse.py ^
        "common/solar_system_initializers/canon/00_attican_traverse_initializers.txt" ^
        "common/solar_system_initializers/canon/btr_attican_traverse"

    python3 Claude-Scripts/split_attican_traverse.py ^
        "common/solar_system_initializers/canon/01_citadel_space_initializers.txt" ^
        "common/solar_system_initializers/canon/btr_council_space"
"""

import re
import os
import sys


def cluster_to_filename(name):
    """Convert a cluster header name like "JAVIS'DAR CLUSTER" to btr_javisdar_cluster.txt"""
    return "btr_" + name.lower().replace("'", "").replace(" ", "_") + ".txt"


def split_initializers(source_file, base_dir):
    with open(source_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_sector = None
    current_cluster = None
    current_cluster_lines = []

    def flush_cluster():
        if not current_sector or not current_cluster or not current_cluster_lines:
            return
        sector_folder = os.path.join(base_dir, f"btr_sector_{current_sector}")
        os.makedirs(sector_folder, exist_ok=True)
        filename = cluster_to_filename(current_cluster)
        filepath = os.path.join(sector_folder, filename)
        content = "".join(current_cluster_lines).rstrip() + "\n"
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            f.write(content)
        print(f"Written: {filepath} ({len(current_cluster_lines)} source lines)")

    i = 0
    while i < len(lines):
        line = lines[i].rstrip('\r\n')

        # Detect all-# separator lines (potential header delimiters)
        if re.match(r'^#+$', line) and len(line) >= 3 and i + 1 < len(lines):
            next_line = lines[i + 1].rstrip('\r\n')

            # Sector header: ##### <Any Name> Sector - <ID> #####
            # Matches AT9, IC1, OC2, etc.
            m = re.match(r'^#{5}\s+.+Sector - ([A-Z]+\d+)\s+#{5}\s*$', next_line)
            if m:
                flush_cluster()
                current_sector = m.group(1).lower()
                current_cluster = None
                current_cluster_lines = []
                i += 3  # skip separator + header + closing separator
                continue

            # Cluster header: ### CLUSTER NAME ### (not 5+ # prefix)
            if current_sector and not re.match(r'^#{5}', next_line):
                m = re.match(r'^###\s+(.+?)\s+###\s*$', next_line)
                if m:
                    flush_cluster()
                    current_cluster = m.group(1)
                    current_cluster_lines = []
                    current_cluster_lines.append(lines[i])        # opening separator
                    current_cluster_lines.append(lines[i + 1])   # cluster name line
                    if i + 2 < len(lines):
                        current_cluster_lines.append(lines[i + 2])  # closing separator
                    i += 3  # skip all 3 header lines
                    continue

        if current_cluster:
            current_cluster_lines.append(lines[i])

        i += 1

    flush_cluster()
    print("Done!")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 split_attican_traverse.py <source_file> <base_dir>")
        sys.exit(1)
    split_initializers(sys.argv[1], sys.argv[2])
