from app.agent.graph import build_graph

def export_png():
    app = build_graph()
    
    png_image = app.get_graph().draw_mermaid_png()
    
    output_path = "langgraph_architecture.png"
    with open(output_path, "wb") as f:
        f.write(png_image)
        
    print(f"✅ Graph successfully exported to {output_path}")

if __name__ == "__main__":
    export_png()