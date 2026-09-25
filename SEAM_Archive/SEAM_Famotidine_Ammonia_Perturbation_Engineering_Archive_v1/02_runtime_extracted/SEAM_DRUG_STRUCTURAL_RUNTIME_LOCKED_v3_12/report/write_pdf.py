from pathlib import Path
import json
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak
from xml.sax.saxutils import escape

GRID=colors.HexColor("#A9A9A9")
HEADER=colors.HexColor("#D9E6F2")
META=colors.HexColor("#E8EEF4")
GREEN=colors.HexColor("#D9EAD3")
YELLOW=colors.HexColor("#FFF2CC")
ORANGE=colors.HexColor("#FCE5CD")
RED=colors.HexColor("#F4CCCC")
WHITE=colors.white
GREY=colors.HexColor("#666666")
TEXT=colors.HexColor("#222222")

def esc(v): return escape(str(v))
def cell(txt,style): return Paragraph(str(txt),style)

def critical_bg(row,primary=False):
    if primary: return GREEN
    return {"INFORMATIONAL":WHITE,"MINOR":YELLOW,"MODERATE":ORANGE,"HIGH":ORANGE,"CRITICAL":RED}.get(row.get("criticality"),WHITE)

def effect_text(row):
    return (f"<b>{esc(row['source_term'])}</b><br/>"
            f"<font color='#444444'>{esc(row['structure'])}</font><br/>"
            f"<font color='#777777'>{esc(row['structural_deviation'])}</font>")

def structural_text(row):
    loc=""
    if "condition_top_entry_index" in row and "response_top_entry_index" in row:
        loc=f"<br/>Manifold localization: {row['condition_top_entry_index']} -> {row['response_top_entry_index']}"
    return (
        f"Pair correspondence: <b>{row.get('pair_correspondence',0):.6f}</b> "
        f"(JS {row.get('pair_js_correspondence',0):.4f}; sign {row.get('pair_sign_continuity',0):.4f})<br/>"
        f"Initial broken: <b>{row['initial_broken_relations']}/{row['constitutive_relation_count']}</b> | "
        f"restored: <b>{row['restored_relations']}</b> | new breaks: <b>{row['new_breaks']}</b><br/>"
        f"Residual broken: {row['residual_broken_relations']}/{row['constitutive_relation_count']} | "
        f"net offset <b>{row['net_offset_change']:+.6f}</b><br/>"
        f"Direction: <b>{esc(row['direction'])}</b>{loc}"
    )

def critical_text(row):
    return f"<b>{esc(row['criticality'])}</b><br/>new-break fraction {row['new_break_fraction']:.4f}"

def effect_table(rows, styles, primary=False):
    h,e,d,c=styles
    data=[[cell("Condition / structure",h),cell("Pair-resolved compound / structure consequence",h),cell("Criticality",h)]]
    for r in rows:
        data.append([cell(effect_text(r),e),cell(structural_text(r),d),cell(critical_text(r),c)])
    t=Table(data,colWidths=[3.05*inch,3.15*inch,1.10*inch],repeatRows=1,hAlign="LEFT")
    cmds=[("BACKGROUND",(0,0),(-1,0),HEADER),("GRID",(0,0),(-1,-1),0.3,GRID),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),3),("RIGHTPADDING",(0,0),(-1,-1),3),("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2)]
    for i,r in enumerate(rows,1): cmds.append(("BACKGROUND",(2,i),(2,i),critical_bg(r,primary=primary)))
    t.setStyle(TableStyle(cmds)); return t

def build_pdf(result_path, output_path):
    r=json.loads(Path(result_path).read_text())
    inp=r["input"]; comp=inp["normalized_compound"]
    primary=r.get("primary_effects",[]); secondary=r.get("secondary_effects",[])
    severe=r.get("high_critical_breaches",[])[:6]
    styles=getSampleStyleSheet()
    title=ParagraphStyle("title",parent=styles["Title"],fontName="Helvetica-Bold",fontSize=15.2,leading=16.5,alignment=TA_CENTER,spaceAfter=2)
    sub=ParagraphStyle("sub",parent=styles["Normal"],fontSize=6.7,leading=7.3,alignment=TA_CENTER,textColor=GREY,spaceAfter=5)
    h2=ParagraphStyle("h2",parent=styles["Heading2"],fontName="Helvetica-Bold",fontSize=10.2,leading=11,spaceBefore=4,spaceAfter=2)
    mh=ParagraphStyle("mh",parent=styles["BodyText"],fontName="Helvetica-Bold",fontSize=6.0,leading=6.6)
    mv=ParagraphStyle("mv",parent=styles["BodyText"],fontSize=6.0,leading=6.6)
    ch=ParagraphStyle("ch",parent=styles["BodyText"],fontSize=5.9,leading=6.6)
    th=ParagraphStyle("th",parent=styles["BodyText"],fontName="Helvetica-Bold",fontSize=5.7,leading=6.2,alignment=TA_CENTER)
    eff=ParagraphStyle("eff",parent=styles["BodyText"],fontSize=5.4,leading=6.0)
    dat=ParagraphStyle("dat",parent=styles["BodyText"],fontSize=5.2,leading=5.8)
    crit=ParagraphStyle("crit",parent=styles["BodyText"],fontSize=5.4,leading=6.0,alignment=TA_CENTER)
    foot=ParagraphStyle("foot",parent=styles["BodyText"],fontSize=5.2,leading=5.9,textColor=TEXT)
    doc=SimpleDocTemplate(str(output_path),pagesize=letter,leftMargin=.55*inch,rightMargin=.55*inch,topMargin=.36*inch,bottomMargin=.38*inch)
    story=[Paragraph("Continuum Bio/Compound Decoder - Pair-Resolved Structural Effect Report",title),Paragraph(f"Run ID: {esc(r['run_id'])}",sub)]
    meta=[
        [cell("Field",mh),cell("Value",mh)],
        [cell("Compound / formulation",mh),cell(esc(r.get("canonical_name") or r["compound_query"]),mv)],
        [cell("Dose",mh),cell(esc(inp["dose"]),mv)],
        [cell("Interval",mh),cell(esc(inp["interval"]),mv)],
        [cell("Daily-equivalent analysis load",mh),cell(f"{r['exposure']['daily_equivalent_analysis_mg']:.6g} mg/day",mv)],
        [cell("Condition/deviation states evaluated independently",mh),cell(str(r['matrix']['condition_rows']),mv)],
        [cell("Parent constitutive reference templates",mh),cell(str(r['matrix']['parent_constitutive_templates']),mv)],
        [cell("Rows with constitutive relation transition",mh),cell(str(r['counts']['rows_with_relation_transition']),mv)],
        [cell("Pair-resolved active hits",mh),cell(str(r['counts'].get('pair_ranked_active_hits',0)),mv)],
    ]
    mt=Table(meta,colWidths=[2.55*inch,4.70*inch],hAlign="LEFT")
    mt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),META),("GRID",(0,0),(-1,-1),.3,GRID),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),3),("RIGHTPADDING",(0,0),(-1,-1),3),("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2)]))
    story += [mt,Paragraph("Resolved Chemical Definition",h2)]
    composition=" ".join(f"{esc(k)}:{v}" for k,v in comp.get("elemental_composition",{}).items())
    proj=r.get("compound_manifold_projection",{})
    chem=(f"<b>{esc(r['chemical_formula'])}</b> | molecular mass {comp['molecular_mass_g_mol']:.5f} g/mol | atoms {comp.get('atom_count','')} ({composition})<br/>"
          f"Compound projection SHA-256: {esc(proj.get('coordinate_sha256',''))}<br/>"
          f"Manifold localization: entry {esc(proj.get('manifold_top_entry_index',''))} | similarity {float(proj.get('manifold_top_similarity',0)):.6f}<br/>"
          f"Execution question: perturb each of the 5,734 represented biological condition/deviation states with this compound signature, then resolve the current compound state against each condition state using the restored pair-correspondence operator. Pair correspondence cannot create a hit. No cross-compound comparison is performed.")
    box=Table([[cell(chem,ch)]],colWidths=[7.25*inch],hAlign="LEFT")
    box.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#F7F7F7")),("BOX",(0,0),(-1,-1),.3,GRID),("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4),("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2)])); story.append(box)
    ts=(th,eff,dat,crit)
    story.append(Paragraph("Primary Pair-Resolved Structural Response",h2)); story.append(effect_table(primary,ts,primary=True) if primary else Paragraph("No row resolved.",eff))
    story.append(Paragraph("Secondary Pair-Resolved Structural Responses",h2)); story.append(effect_table(secondary[:7],ts) if secondary else Paragraph("No secondary rows resolved.",eff))
    if severe:
        story.append(Paragraph("Additional High / Critical New-Break Responses",h2)); story.append(effect_table(severe[:4],ts))
    legend=Table([
        [cell("PRIMARY",crit),cell("INFORMATIONAL",crit),cell("MINOR",crit),cell("MODERATE/HIGH",crit),cell("CRITICAL",crit)],
        [cell("highest pair correspondence among active structural transitions",foot),cell("no new constitutive break",foot),cell("new-break fraction <= 0.25",foot),cell("larger new-break fraction",foot),cell("all local reference relations newly broken",foot)],
    ],colWidths=[1.45*inch]*5,hAlign="CENTER")
    legend.setStyle(TableStyle([("BACKGROUND",(0,0),(0,0),GREEN),("BACKGROUND",(1,0),(1,0),WHITE),("BACKGROUND",(2,0),(2,0),YELLOW),("BACKGROUND",(3,0),(3,0),ORANGE),("BACKGROUND",(4,0),(4,0),RED),("GRID",(0,0),(-1,-1),.25,GRID),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("ALIGN",(0,0),(-1,-1),"CENTER"),("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2)]))
    story += [Spacer(1,4),legend]
    def footer_page(canvas, doc_obj):
        canvas.saveState(); canvas.setFont("Helvetica",5.1); canvas.setFillColor(TEXT)
        canvas.drawString(.55*inch,.22*inch,"Analysis output only. Each condition state is perturbed independently, then pair-resolved against the current compound; pair score cannot create a hit. Criticality is structural, not clinical guidance.")
        canvas.restoreState()
    doc.build(story,onFirstPage=footer_page,onLaterPages=footer_page)
    return str(output_path)
