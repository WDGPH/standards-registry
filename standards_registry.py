import gradio as gr
import yaml
import json
from pathlib import Path
from dataclasses import dataclass

@dataclass
class Standard:
    id: str
    title: str
    description: str
    path: str
    version: str
    maintainer: str
    last_updated: str
    source: dict = None
    tags: list = None

class StandardsRegistry:
    def __init__(self, registry_path: Path):
        self.registry_path = registry_path
        self.standards = {}
        self.data_cache = {}
        self._load_registry()
    
    def _load_registry(self):
        registry_file = self.registry_path / "registry.yaml"
        if not registry_file.exists():
            return
        
        with open(registry_file, "r") as f:
            registry_data = yaml.safe_load(f)
        
        for item in registry_data.get("registry", []):
            standard = Standard(
                id=item.get("id", ""),
                title=item.get("title", ""),
                description=item.get("description", ""),
                path=item.get("path", ""),
                version=item.get("version", ""),
                maintainer=item.get("maintainer", ""),
                last_updated=item.get("last_updated", ""),
                source=item.get("source"),
                tags=item.get("tags", [])
            )
            self.standards[standard.id] = standard
    
    def get_standard(self, standard_id: str):
        return self.standards.get(standard_id)
    
    def list_standards(self):
        return list(self.standards.values())
    
    def load_standard_data(self, standard_id: str):
        if standard_id in self.data_cache:
            return self.data_cache[standard_id]
        
        standard = self.get_standard(standard_id)
        if not standard:
            return None
        
        data_path = self.registry_path / standard.path
        path_parts = standard.path.split("/")
        filename = path_parts[-1]
        dir_path = "/".join(path_parts[:-1])
        
        # Special handling for school_boards with multiple possible data sources
        if standard_id == "school_boards":
            json_paths = [
                self.registry_path / "data" / "school_boards_with_acronyms.json",
                self.registry_path / "data" / "20251030_school_boards.json",
            ]
            for json_path in json_paths:
                if not json_path.exists():
                    continue
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    records = self._get_data_records(data)
                    if records:
                        self.data_cache[standard_id] = data
                        return data
            return None
        
        # Try multiple path variations for data files
        possible_paths = [
            data_path,
            self.registry_path / dir_path / f"20251030_{filename}",
            self.registry_path / dir_path / filename.replace(".yaml", ".json"),
        ]
        
        found_path = next((p for p in possible_paths if p.exists()), None)
        if not found_path:
            return None
        
        with open(found_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) if found_path.suffix == ".yaml" else json.load(f)
        
        if not data:
            return None
        
        records = self._get_data_records(data)
        if not records:
            return None
        
        self.data_cache[standard_id] = data
        return data
    
    def _get_data_records(self, data):
        if not data:
            return []
        
        if "standard" in data and "data" in data["standard"]:
            return data["standard"]["data"]
        elif "data" in data:
            return data["data"]
        elif "records" in data:
            fields = [f["id"] for f in data.get("fields", [])]
            if not fields:
                return []
            return [dict(zip(fields, record)) for record in data["records"]]
        return []
    
    def search_records(self, standard_id: str, query: str):
        data = self.load_standard_data(standard_id)
        if not data:
            return []
        
        records = self._get_data_records(data)
        if not records:
            return []
        
        query_lower = query.lower()
        return [r for r in records if query_lower in " ".join(str(v) for v in r.values() if v).lower()]
    
    def get_statistics(self, standard_id: str):
        data = self.load_standard_data(standard_id)
        if not data:
            return {}
        
        records = self._get_data_records(data)
        if not records:
            return {}
        
        return {"total_records": len(records), "fields": list(records[0].keys())}

def format_standard_info(standard: Standard):
    info = f"# {standard.title}\n\n"
    info += f"**ID:** `{standard.id}`\n\n"
    info += f"**Description:** {standard.description}\n\n"
    info += f"**Version:** {standard.version}\n\n"
    info += f"**Maintainer:** {standard.maintainer}\n\n"
    info += f"**Last Updated:** {standard.last_updated}\n\n"
    
    if standard.source:
        info += f"**Source:** [{standard.source.get('name', 'N/A')}]({standard.source.get('url', '#')})\n\n"
    
    if standard.tags:
        tags_str = ", ".join(f"`{tag}`" for tag in standard.tags)
        info += f"**Tags:** {tags_str}\n\n"
    
    return info

def create_registry_overview(registry: StandardsRegistry):
    standards = registry.list_standards()
    if not standards:
        return "No standards found in registry."
    
    total_records = 0
    for std in standards:
        stats = registry.get_statistics(std.id)
        total_records += stats.get("total_records", 0)
    
    overview = "# Registry Overview\n\n"
    overview += f"**Total Standards:** {len(standards)}\n\n"
    overview += f"**Total Records:** {total_records:,}\n\n"
    overview += "---\n\n"
    
    for std in standards:
        stats = registry.get_statistics(std.id)
        record_count = stats.get("total_records", 0)
        
        overview += f"## {std.title}\n\n"
        overview += f"**ID:** `{std.id}`  \n"
        overview += f"**Version:** {std.version}  \n"
        overview += f"**Last Updated:** {std.last_updated}  \n"
        overview += f"**Records:** {record_count:,}\n"
        if std.tags:
            tags_str = ", ".join(f"`{tag}`" for tag in std.tags)
            overview += f"**Tags:** {tags_str}\n"
        overview += f"**Description:** {std.description[:150]}...\n\n"
        overview += "---\n\n"
    
    return overview

def get_standard_details(standard_id: str, registry: StandardsRegistry):
    if not standard_id:
        return "Please select a standard.", "", ""
    
    standard = registry.get_standard(standard_id)
    if not standard:
        return "Standard not found.", "", ""
    
    info = format_standard_info(standard)
    
    stats = registry.get_statistics(standard_id)
    stats_text = ""
    if stats:
        stats_text = "## Statistics\n\n"
        stats_text += f"**Total Records:** {stats.get('total_records', 0):,}  \n"
        if stats.get("fields"):
            stats_text += f"**Fields:** {len(stats['fields'])}  \n"
            stats_text += f"**Field Names:** {', '.join(stats['fields'][:10])}"
            if len(stats['fields']) > 10:
                stats_text += f" *(+{len(stats['fields']) - 10} more)*"
        stats_text += "\n"
    
    data = registry.load_standard_data(standard_id)
    data_preview = ""
    
    if data:
        records = registry._get_data_records(data)
        if records:
            preview_count = min(10, len(records))
            data_preview = f"**Data Preview (showing {preview_count} of {len(records)} records):**\n\n"
            for i, record in enumerate(records[:10], 1):
                data_preview += f"### Record {i}\n\n"
                for key, value in record.items():
                    if value:
                        data_preview += f"**{key}:** {value}  \n"
                data_preview += "\n"
    
    return info, stats_text, data_preview

def search_standard_records(standard_id: str, query: str, registry: StandardsRegistry):
    if not standard_id:
        return "Please select a standard first."
    
    if not query:
        return "Please enter a search query."
    
    results = registry.search_records(standard_id, query)
    
    if not results:
        return f"No results found for '{query}' in {registry.get_standard(standard_id).title}."
    
    output = f"**Found {len(results)} result(s) for '{query}':**\n\n"
    output += "---\n\n"
    
    for i, result in enumerate(results[:50], 1):
        output += f"### Result {i}\n\n"
        if isinstance(result, dict):
            for key, value in result.items():
                if value:
                    output += f"**{key}:** {value}  \n"
        else:
            output += f"{result}\n"
        output += "\n---\n\n"
    
    if len(results) > 50:
        output += f"\n*Showing first 50 of {len(results)} results.*\n"
    
    return output

def format_cell_value(value, max_length=50):
    if value is None:
        return ""
    value_str = str(value)
    return value_str[:max_length] + "..." if len(value_str) > max_length else value_str

def format_header(header: str):
    return header.replace("_", " ").title().replace("Id", "ID")

def get_all_records_table(standard_id: str, registry: StandardsRegistry):
    if not standard_id:
        return []
    
    data = registry.load_standard_data(standard_id)
    if not data:
        return []
    
    records = registry._get_data_records(data)
    if not records or not records[0]:
        return []
    
    fields = list(records[0].keys())
    if not fields:
        return []
    
    table_data = [[format_header(f) for f in fields]]
    
    for record in records:
        row = []
        for f in fields:
            value = record.get(f)
            if value is None:
                row.append("—")
            elif isinstance(value, str):
                row.append(value.strip() or "—")
            elif isinstance(value, (int, float)):
                row.append(f"{value:,}" if isinstance(value, int) else f"{value:.2f}")
            else:
                row.append(str(value))
        table_data.append(row)
    
    return table_data

def get_all_records_html_table(standard_id: str, registry: StandardsRegistry):
    from html import escape
    
    if not standard_id:
        return "<div class='table-container'><p>Please select a standard.</p></div>"
    
    data = registry.load_standard_data(standard_id)
    if not data:
        return "<div class='table-container'><p>No data available.</p></div>"
    
    records = registry._get_data_records(data)
    if not records or not records[0]:
        return "<div class='table-container'><p>No records found.</p></div>"
    
    fields = list(records[0].keys())
    if not fields:
        return "<div class='table-container'><p>No fields found.</p></div>"
    
    html_output = '<div class="table-wrapper"><table class="data-table"><thead><tr>'
    for field in fields:
        header = format_header(field)
        html_output += f'<th>{escape(header)}</th>'
    html_output += '</tr></thead><tbody>'
    
    for record in records:
        html_output += '<tr>'
        for field in fields:
            value = record.get(field)
            if value is None:
                cell_value = "—"
            elif isinstance(value, str):
                cell_value = value.strip() or "—"
            elif isinstance(value, (int, float)):
                cell_value = f"{value:,}" if isinstance(value, int) else f"{value:.2f}"
            else:
                cell_value = str(value)
            html_output += f'<td>{escape(cell_value)}</td>'
        html_output += '</tr>'
    
    html_output += '</tbody></table></div>'
    return html_output

def main():
    registry_path = Path(__file__).parent
    registry = StandardsRegistry(registry_path)
    
    standard_ids = [std.id for std in registry.list_standards()]
    
    custom_css = """
    .table-wrapper {
        overflow-x: auto !important;
        overflow-y: auto !important;
        width: 100% !important;
        max-height: 700px !important;
        border: 1px solid #d1d5db !important;
        border-radius: 8px !important;
        position: relative !important;
        background: #ffffff !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    .table-wrapper::-webkit-scrollbar {
        height: 12px !important;
        width: 12px !important;
    }
    .table-wrapper::-webkit-scrollbar-track {
        background: #f1f1f1 !important;
        border-radius: 6px !important;
    }
    .table-wrapper::-webkit-scrollbar-thumb {
        background: #888 !important;
        border-radius: 6px !important;
    }
    .table-wrapper::-webkit-scrollbar-thumb:hover {
        background: #555 !important;
    }
    .data-table {
        width: max-content !important;
        min-width: 100% !important;
        border-collapse: collapse !important;
        border-spacing: 0 !important;
        font-size: 13px !important;
        table-layout: auto !important;
        margin: 0 !important;
    }
    .data-table th,
    .data-table td {
        min-width: 120px !important;
        max-width: none !important;
        width: auto !important;
        white-space: normal !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        padding: 12px 16px !important;
        text-align: left !important;
        border: 1px solid #d1d5db !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
        vertical-align: top !important;
    }
    .data-table th {
        background-color: #374151 !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        position: sticky !important;
        top: 0 !important;
        z-index: 10 !important;
        font-size: 14px !important;
        text-transform: none !important;
        letter-spacing: 0.3px !important;
        white-space: nowrap !important;
        border-bottom: 2px solid #1f2937 !important;
    }
    .data-table td {
        background-color: #ffffff !important;
        color: #111827 !important;
    }
    .data-table td:hover {
        background-color: #f3f4f6 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
        z-index: 5 !important;
        position: relative !important;
        color: #111827 !important;
    }
    .data-table tr:nth-child(even) td {
        background-color: #f9fafb !important;
        color: #111827 !important;
    }
    .data-table tr:nth-child(even) td:hover {
        background-color: #f3f4f6 !important;
        color: #111827 !important;
    }
    .data-table tr:hover td {
        background-color: #f3f4f6 !important;
        color: #111827 !important;
    }
    .data-table tr:hover td:hover {
        background-color: #e5e7eb !important;
        color: #111827 !important;
    }
    .gradio-container {
        max-width: 1800px !important;
        margin: 0 auto;
    }
    h1 {
        font-weight: 300;
        letter-spacing: -0.5px;
        margin-bottom: 0.5em;
    }
    .markdown-text {
        line-height: 1.7;
    }
    """
    
    theme = gr.themes.Default(
        primary_hue="slate",
        font=("Inter", "system-ui", "sans-serif"),
        spacing_size="md",
        radius_size="md"
    )
    
    with gr.Blocks(title="Standards Registry", theme=theme, css=custom_css) as app:
        gr.Markdown(
            """
            # Standards Registry
            
            Version-controlled registry of standards for WDGPH automation and data engineering projects.
            
            This registry provides a single source of truth for maintaining consistent schemas, naming conventions, 
            validation rules, and reference metadata across systems, teams, and environments.
            """,
            elem_classes=["markdown-text"]
        )
        
        with gr.Tabs():
            with gr.Tab("Overview"):
                overview_text = gr.Markdown(create_registry_overview(registry), elem_classes=["markdown-text"])
                refresh_btn = gr.Button("Refresh", variant="secondary")
                refresh_btn.click(
                    fn=lambda: create_registry_overview(registry),
                    outputs=overview_text
                )
            
            with gr.Tab("Browse"):
                with gr.Row():
                    with gr.Column(scale=1):
                        standard_dropdown = gr.Dropdown(
                            choices=standard_ids,
                            label="Standard",
                            interactive=True
                        )
                        refresh_standard_btn = gr.Button("Load Details", variant="primary")
                    
                    with gr.Column(scale=2):
                        standard_info = gr.Markdown("Select a standard to view details.", elem_classes=["markdown-text"])
                        standard_stats = gr.Markdown("", elem_classes=["markdown-text"])
                        data_preview = gr.Markdown("", elem_classes=["markdown-text"])
                
                refresh_standard_btn.click(
                    fn=lambda sid: get_standard_details(sid, registry),
                    inputs=standard_dropdown,
                    outputs=[standard_info, standard_stats, data_preview]
                )
                standard_dropdown.change(
                    fn=lambda sid: get_standard_details(sid, registry),
                    inputs=standard_dropdown,
                    outputs=[standard_info, standard_stats, data_preview]
                )
            
            with gr.Tab("Data"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### Controls", elem_classes=["markdown-text"])
                        table_standard_dropdown = gr.Dropdown(
                            choices=standard_ids,
                            label="Standard",
                            interactive=True
                        )
                        load_table_btn = gr.Button("Load Table", variant="primary", size="lg")
                        gr.Markdown("---")
                        table_info = gr.Markdown("", elem_classes=["markdown-text"])
                    
                    with gr.Column(scale=4):
                        table_status = gr.Markdown(
                            "### Data Table\n\nSelect a standard and click 'Load Table' to view data.",
                            elem_classes=["markdown-text"]
                        )
                        data_table = gr.HTML(label="")
                
                def load_table_with_status(sid):
                    if not sid:
                        return "<div class='table-container'><p>Please select a standard.</p></div>", "Please select a standard.", ""
                    
                    standard = registry.get_standard(sid)
                    standard_title = standard.title if standard else "selected standard"
                    
                    data = registry.load_standard_data(sid)
                    if not data:
                        info_text = f"**Standard:** {standard_title}\n\n**Status:** No data available"
                        return "<div class='table-container'><p>No data available.</p></div>", f"### No Data Available\n\nNo data found for {standard_title}.", info_text
                    
                    records = registry._get_data_records(data)
                    if not records:
                        info_text = f"**Standard:** {standard_title}\n\n**Status:** No records found"
                        return "<div class='table-container'><p>No records found.</p></div>", f"### No Records\n\nNo records found for {standard_title}.", info_text
                    
                    record_count = len(records)
                    field_count = len(records[0].keys()) if records else 0
                    
                    html_table = get_all_records_html_table(sid, registry)
                    
                    info_text = f"""
**Standard:** {standard_title}

**Records:** {record_count:,}

**Fields:** {field_count}

**Status:** Loaded successfully
"""
                    status_text = f"### Data Loaded\n\n{record_count:,} records with {field_count} fields loaded from {standard_title}."
                    return html_table, status_text, info_text
                
                load_table_btn.click(
                    fn=load_table_with_status,
                    inputs=table_standard_dropdown,
                    outputs=[data_table, table_status, table_info]
                )
                table_standard_dropdown.change(
                    fn=lambda sid: ("<div class='table-container'><p>Select a standard and click 'Load Table' to view data.</p></div>", f"### Data Table\n\nSelected: {registry.get_standard(sid).title if sid else 'None'}. Click 'Load Table' to view data.", ""),
                    inputs=table_standard_dropdown,
                    outputs=[data_table, table_status, table_info]
                )
            
            with gr.Tab("Search"):
                with gr.Row():
                    with gr.Column(scale=1):
                        search_standard_dropdown = gr.Dropdown(
                            choices=standard_ids,
                            label="Standard",
                            interactive=True
                        )
                        search_query = gr.Textbox(
                            label="Search Query",
                            placeholder="Enter search term...",
                            interactive=True
                        )
                        search_btn = gr.Button("Search", variant="primary")
                    
                    with gr.Column(scale=2):
                        search_results = gr.Markdown("Enter a search query to find records.", elem_classes=["markdown-text"])
                
                search_btn.click(
                    fn=lambda sid, q: search_standard_records(sid, q, registry),
                    inputs=[search_standard_dropdown, search_query],
                    outputs=search_results
                )
                search_query.submit(
                    fn=lambda sid, q: search_standard_records(sid, q, registry),
                    inputs=[search_standard_dropdown, search_query],
                    outputs=search_results
                )
        
        gr.Markdown("---\n\n*Standards Registry - WDGPH Information Systems & Digital Innovation*", elem_classes=["markdown-text"])
    
    return app

if __name__ == "__main__":
    import signal
    import sys
    
    app = main()
    
    def signal_handler(sig, frame):
        print("\nShutting down server...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        app.launch(share=False, server_name="0.0.0.0", server_port=7860)
    except KeyboardInterrupt:
        print("\nShutting down server...")
        sys.exit(0)

