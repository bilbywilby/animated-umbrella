import json

def generate_markdown():
    with open("market_data.json", "r") as f:
        data = json.load(f)
    
    avg = data["statewide_averages"]
    
    md = f"# Pennsylvania ACA 2027 Market Assessment\n\n"
    md += "## Executive Summary\n"
    md += f"The 2027 individual market is seeing a weighted approved increase of **{avg['individual']['approved']}%**, "
    md += f"slightly lower than the requested **{avg['individual']['requested']}%**. "
    md += f"The small group market is more stable at **{avg['small_group']['approved']}%** approved.\n\n"
    
    md += "## Carrier Breakdown\n"
    md += "| Carrier | Requested % | Approved % | Variance |\n"
    md += "| :--- | :---: | :---: | :---: |\n"
    
    for c in data["carriers"]:
        variance = c["approved"] - c["requested"]
        md += f"| {c['name']} | {c['requested']}% | {c['approved']}% | {variance:+.2f}% |\n"
    
    with open("ACA_2027_Briefing.md", "w") as f:
        f.write(md)
    print("User-friendly documentation generated: ACA_2027_Briefing.md. Quack!")

if __name__ == "__main__":
    generate_markdown()
