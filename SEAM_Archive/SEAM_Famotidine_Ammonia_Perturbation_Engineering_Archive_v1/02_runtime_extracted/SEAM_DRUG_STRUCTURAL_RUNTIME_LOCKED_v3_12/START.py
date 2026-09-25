#!/usr/bin/env python3
import argparse
from engine.run import run

def main():
    p=argparse.ArgumentParser(description="Continuum Bio/Compound Decoder - 5,734 independent perturbations with restored pair resolution")
    p.add_argument("--compound"); p.add_argument("--dose"); p.add_argument("--interval"); p.add_argument("--output-dir")
    a=p.parse_args()
    compound=a.compound or input("What chemical formula or drug name? ").strip()
    dose=a.dose or input("What dosage? ").strip()
    interval=a.interval or input("What interval? ").strip()
    r=run(compound,dose,interval,a.output_dir,make_pdf=True)
    print(f"RUN COMPLETE: {r['matrix']['condition_rows']} condition states / {r['counts']['rows_with_relation_transition']} structural transitions / {r['counts']['pair_ranked_active_hits']} pair-resolved active hits")
    print("RESULT:",r.get("report_path",""))
if __name__=="__main__": main()
