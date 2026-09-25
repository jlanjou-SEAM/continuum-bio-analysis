#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <errno.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <limits.h>
#include <unistd.h>

#define DIMS 128
#define EPS 1e-15
#define MAGIC "SPCLOS1"

typedef struct { uint8_t a,b; int8_t rel; uint8_t pad; } Pair;
typedef struct {
    uint32_t name_off, pair_off, pair_count, needed_count;
    int32_t base_top;
    double T[DIMS];
    const char *name;
} Structure;
typedef struct {
    char baseline_id[8];
    uint16_t structure_idx, reserved;
    uint32_t deviation_off, term_off, partition_off;
    const char *deviation, *term, *partition;
} Row;
typedef struct {
    uint32_t needed_count, relation_count, broken;
    int32_t base_top, compound_top;
    double break_fraction, closure_load;
    int tier_order;
    const char *tier;
} Result;
typedef struct {
    uint32_t version,dims,manifold_count,structure_count,row_count,pair_count,pool_size;
    double *G, *S;
    Structure *structures;
    Pair *pairs;
    Row *rows;
    char *pool;
} LockData;

static void die(const char *msg){ fprintf(stderr,"ERROR: %s\n",msg); exit(2); }
static void die_errno(const char *msg){ fprintf(stderr,"ERROR: %s: %s\n",msg,strerror(errno)); exit(2); }

static uint32_t rd_u32(FILE *f){ uint8_t b[4]; if(fread(b,1,4,f)!=4) die("short lock read"); return (uint32_t)b[0]|((uint32_t)b[1]<<8)|((uint32_t)b[2]<<16)|((uint32_t)b[3]<<24); }
static int32_t rd_i32(FILE *f){ return (int32_t)rd_u32(f); }
static uint16_t rd_u16(FILE *f){ uint8_t b[2]; if(fread(b,1,2,f)!=2) die("short lock read"); return (uint16_t)(b[0]|((uint16_t)b[1]<<8)); }
static double rd_f64(FILE *f){ union { uint64_t u; double d; } x; uint8_t b[8]; if(fread(b,1,8,f)!=8) die("short lock read"); x.u=0; for(int i=0;i<8;i++) x.u|=((uint64_t)b[i])<<(8*i); return x.d; }

static LockData load_lock(const char *path){
    LockData d; memset(&d,0,sizeof(d));
    FILE *f=fopen(path,"rb"); if(!f) die_errno("cannot open lock file");
    char magic[8]; if(fread(magic,1,8,f)!=8) die("short lock header");
    if(memcmp(magic,MAGIC,7)!=0) die("invalid lock magic");
    d.version=rd_u32(f); d.dims=rd_u32(f); d.manifold_count=rd_u32(f); d.structure_count=rd_u32(f); d.row_count=rd_u32(f); d.pair_count=rd_u32(f); d.pool_size=rd_u32(f);
    if(d.version!=1 || d.dims!=DIMS || d.structure_count!=420 || d.row_count!=5734) die("unexpected lock dimensions/counts");
    d.G=(double*)calloc(DIMS,sizeof(double)); d.S=(double*)calloc((size_t)d.manifold_count*DIMS,sizeof(double));
    d.structures=(Structure*)calloc(d.structure_count,sizeof(Structure)); d.pairs=(Pair*)calloc(d.pair_count,sizeof(Pair)); d.rows=(Row*)calloc(d.row_count,sizeof(Row)); d.pool=(char*)calloc(d.pool_size,1);
    if(!d.G||!d.S||!d.structures||!d.pairs||!d.rows||!d.pool) die("out of memory");
    for(int j=0;j<DIMS;j++) d.G[j]=rd_f64(f);
    for(size_t i=0;i<(size_t)d.manifold_count*DIMS;i++) d.S[i]=rd_f64(f);
    for(uint32_t i=0;i<d.structure_count;i++){
        Structure *s=&d.structures[i]; s->name_off=rd_u32(f); s->pair_off=rd_u32(f); s->pair_count=rd_u32(f); s->needed_count=rd_u32(f); s->base_top=rd_i32(f);
        for(int j=0;j<DIMS;j++) s->T[j]=rd_f64(f);
    }
    for(uint32_t i=0;i<d.pair_count;i++){
        int a=fgetc(f),b=fgetc(f),r=fgetc(f),p=fgetc(f); if(a<0||b<0||r<0||p<0) die("short pair read");
        d.pairs[i].a=(uint8_t)a; d.pairs[i].b=(uint8_t)b; d.pairs[i].rel=(int8_t)(uint8_t)r; d.pairs[i].pad=(uint8_t)p;
    }
    for(uint32_t i=0;i<d.row_count;i++){
        Row *r=&d.rows[i]; if(fread(r->baseline_id,1,8,f)!=8) die("short row read"); r->structure_idx=rd_u16(f); r->reserved=rd_u16(f); r->deviation_off=rd_u32(f); r->term_off=rd_u32(f); r->partition_off=rd_u32(f);
        if(r->structure_idx>=d.structure_count) die("invalid structure index");
    }
    if(fread(d.pool,1,d.pool_size,f)!=d.pool_size) die("short string pool read");
    fclose(f);
    for(uint32_t i=0;i<d.structure_count;i++){ if(d.structures[i].name_off>=d.pool_size) die("bad string offset"); d.structures[i].name=d.pool+d.structures[i].name_off; }
    for(uint32_t i=0;i<d.row_count;i++){
        Row *r=&d.rows[i]; if(r->deviation_off>=d.pool_size||r->term_off>=d.pool_size||r->partition_off>=d.pool_size) die("bad row string offset");
        r->deviation=d.pool+r->deviation_off; r->term=d.pool+r->term_off; r->partition=d.pool+r->partition_off;
    }
    return d;
}

static void free_lock(LockData *d){ free(d->G); free(d->S); free(d->structures); free(d->pairs); free(d->rows); free(d->pool); memset(d,0,sizeof(*d)); }

static void surface_signature(const uint8_t *payload,size_t n,double out[DIMS]){
    double comp[64]={0}, rel[64]={0};
    uint8_t *seq=(uint8_t*)malloc((n*4/3)+8); if(!seq) die("out of memory"); size_t m=0;
    size_t i=0;
    while(i+3<=n){ uint32_t v=((uint32_t)payload[i]<<16)|((uint32_t)payload[i+1]<<8)|payload[i+2]; seq[m++]=(v>>18)&63; seq[m++]=(v>>12)&63; seq[m++]=(v>>6)&63; seq[m++]=v&63; i+=3; }
    size_t rem=n-i;
    if(rem==1){ uint32_t v=((uint32_t)payload[i]<<16); seq[m++]=(v>>18)&63; seq[m++]=(v>>12)&63; }
    else if(rem==2){ uint32_t v=((uint32_t)payload[i]<<16)|((uint32_t)payload[i+1]<<8); seq[m++]=(v>>18)&63; seq[m++]=(v>>12)&63; seq[m++]=(v>>6)&63; }
    for(size_t k=0;k<m;k++) comp[seq[k]]+=1.0;
    if(m){ for(int j=0;j<64;j++) comp[j]/=(double)m; }
    if(m>1){ for(size_t k=1;k<m;k++){ int x=(int)seq[k]-(int)seq[k-1]; if(x<0)x=-x; rel[x]+=1.0; } for(int j=0;j<64;j++) rel[j]/=(double)(m-1); }
    double sum=0; for(int j=0;j<64;j++){ out[j]=comp[j]; out[64+j]=rel[j]; sum+=comp[j]+rel[j]; }
    if(sum>0){ for(int j=0;j<DIMS;j++) out[j]/=sum; }
    free(seq);
}


typedef struct { const char *sym; double aw; } ElementWeight;
static const ElementWeight element_weights[] = {
    {"H",1.00794},{"He",4.002602},{"Li",6.941},{"Be",9.012182},{"B",10.811},{"C",12.0107},{"N",14.0067},{"O",15.9994},{"F",18.9984032},{"Ne",20.1797},
    {"Na",22.98976928},{"Mg",24.3050},{"Al",26.9815386},{"Si",28.0855},{"P",30.973762},{"S",32.065},{"Cl",35.453},{"Ar",39.948},{"K",39.0983},{"Ca",40.078},
    {"Sc",44.955912},{"Ti",47.867},{"V",50.9415},{"Cr",51.9961},{"Mn",54.938045},{"Fe",55.845},{"Co",58.933195},{"Ni",58.6934},{"Cu",63.546},{"Zn",65.38},
    {"Ga",69.723},{"Ge",72.64},{"As",74.92160},{"Se",78.96},{"Br",79.904},{"Kr",83.798},{"Rb",85.4678},{"Sr",87.62},{"Ag",107.8682},{"Cd",112.411},
    {"Sn",118.710},{"Sb",121.760},{"Te",127.60},{"I",126.90447},{"Ba",137.327},{"Pt",195.084},{"Au",196.966569},{"Hg",200.59},{"Pb",207.2}
};

static double atomic_weight_for(const char *sym){
    size_t n=sizeof(element_weights)/sizeof(element_weights[0]);
    for(size_t i=0;i<n;i++) if(strcmp(sym,element_weights[i].sym)==0) return element_weights[i].aw;
    return -1.0;
}

static double molecular_weight_from_formula(const char *formula){
    const char *p=formula; double mw=0.0; int atoms=0;
    while(*p){
        if(*p<'A'||*p>'Z') return -1.0;
        char sym[3]={0,0,0}; sym[0]=*p++;
        if(*p>='a'&&*p<='z') sym[1]=*p++;
        long count=0;
        while(*p>='0'&&*p<='9'){ count=count*10+(*p-'0'); p++; }
        if(count==0) count=1;
        double aw=atomic_weight_for(sym); if(aw<=0.0) return -1.0;
        mw += aw*(double)count; atoms += (int)count;
    }
    return atoms>0?mw:-1.0;
}

static double parse_dose_mg(const char *dose){
    char *end=NULL; errno=0; double v=strtod(dose,&end);
    if(errno||end==dose||!isfinite(v)||v<0.0) return -1.0;
    while(*end==' '||*end=='\t') end++;
    char unit[16]={0}; size_t u=0;
    while(*end && u<sizeof(unit)-1){ char c=*end++; if(c!=' '&&c!='\t') unit[u++]=(char)((c>='A'&&c<='Z')?c+32:c); }
    unit[u]=0;
    if(unit[0]==0||strcmp(unit,"mg")==0) return v;
    if(strcmp(unit,"g")==0) return v*1000.0;
    if(strcmp(unit,"ug")==0||strcmp(unit,"mcg")==0||strcmp(unit,"µg")==0) return v/1000.0;
    if(strcmp(unit,"ng")==0) return v/1000000.0;
    return -1.0;
}

/* Continuous loading coordinate: millimoles administered.
   Since mg / (g/mol) = mmol, this converts mass dose to molecule-count-proportional loading
   without changing the compound identity vector. */
static double compound_loading_mmol(const char *formula,const char *dose,double *mw_out,double *mg_out){
    double mw=molecular_weight_from_formula(formula); if(mw<=0.0) return -1.0;
    double mg=parse_dose_mg(dose); if(mg<0.0) return -1.0;
    if(mw_out) *mw_out=mw;
    if(mg_out) *mg_out=mg;
    return mg/mw;
}

static int relation(double a,double b){ double z=fabs(a-b); if(z<=1e-12) return 0; return a<b?-1:1; }

static int js_argmax(const double C[DIMS], const double *S, uint32_t nrows){
    double A[DIMS], asum=0; for(int j=0;j<DIMS;j++){ A[j]=C[j]<EPS?EPS:C[j]; asum+=A[j]; } for(int j=0;j<DIMS;j++) A[j]/=asum;
    double best=-1.0; int besti=0;
    for(uint32_t i=0;i<nrows;i++){
        double bsum=0; const double *sr=S+(size_t)i*DIMS; double B[DIMS];
        for(int j=0;j<DIMS;j++){ B[j]=sr[j]<EPS?EPS:sr[j]; bsum+=B[j]; } for(int j=0;j<DIMS;j++) B[j]/=bsum;
        double klA=0,klB=0;
        for(int j=0;j<DIMS;j++){ double M=(A[j]+B[j])*0.5; klA+=A[j]*(log(A[j]/M)/log(2.0)); klB+=B[j]*(log(B[j]/M)/log(2.0)); }
        double sim=1.0-0.5*(klA+klB); if(sim<0)sim=0; else if(sim>1)sim=1;
        if(sim>best){ best=sim; besti=(int)i; }
    }
    return besti;
}

static Result resolve_structure(const LockData *d,const Structure *s,const double Q[DIMS],double loading){
    Result r; memset(&r,0,sizeof(r)); double C[DIMS],sum=0;
    for(int j=0;j<DIMS;j++){ double v=s->T[j]+loading*(Q[j]-d->G[j]); if(v<EPS)v=EPS; C[j]=v; sum+=v; }
    for(int j=0;j<DIMS;j++) C[j]/=sum;
    uint32_t broken=0; for(uint32_t k=0;k<s->pair_count;k++){ const Pair *p=&d->pairs[s->pair_off+k]; if(relation(C[p->a],C[p->b])!=(int)p->rel) broken++; }
    r.needed_count=s->needed_count; r.relation_count=s->pair_count; r.broken=broken; r.base_top=s->base_top; r.compound_top=js_argmax(C,d->S,d->manifold_count);
    r.break_fraction=s->pair_count?((double)broken/(double)s->pair_count):0.0; r.closure_load=(broken&&s->pair_count)?r.break_fraction*log1p((double)s->pair_count):0.0;
    if(!broken){ r.tier="NONE"; r.tier_order=0; }
    else if(r.break_fraction<=0.25){ r.tier="LOW"; r.tier_order=1; }
    else if(r.break_fraction<=0.50){ r.tier="MEDIUM"; r.tier_order=2; }
    else if(r.break_fraction<1.0){ r.tier="HIGH"; r.tier_order=3; }
    else { r.tier="CRITICAL"; r.tier_order=4; }
    return r;
}

static void csv_field(FILE *f,const char *s){ int quote=0; for(const char *p=s;*p;p++) if(*p==','||*p=='"'||*p=='\n'||*p=='\r'){quote=1;break;} if(!quote){fputs(s,f);return;} fputc('"',f); for(const char *p=s;*p;p++){ if(*p=='"')fputc('"',f); fputc(*p,f);} fputc('"',f); }

static const LockData *cmp_d; static const Result *cmp_res;
static int hit_cmp(const void *aa,const void *bb){
    uint32_t a=*(const uint32_t*)aa,b=*(const uint32_t*)bb; const Row *ra=&cmp_d->rows[a], *rb=&cmp_d->rows[b]; const Result *xa=&cmp_res[ra->structure_idx],*xb=&cmp_res[rb->structure_idx];
    if(xa->tier_order!=xb->tier_order) return xb->tier_order-xa->tier_order;
    if(xa->closure_load<xb->closure_load) return 1;
    if(xa->closure_load>xb->closure_load) return -1;
    return strcmp(ra->baseline_id,rb->baseline_id);
}

static void write_header(FILE *f,int ranked){
    fputs("baseline_id,structure,structural_deviation,source_term,source_partition,necessary_coordinate_count,constitutive_relation_count,constitutive_relations_broken,closure_broken,baseline_top_entry_index,compound_top_entry_index,localization_identity_preserved,break_fraction,closure_load,tier,tier_order",f); if(ranked) fputs(",blind_rank",f); fputc('\n',f);
}
static void write_row(FILE *f,const LockData *d,const Result *results,uint32_t ri,int ranked,uint32_t rank){
    const Row *row=&d->rows[ri]; const Structure *s=&d->structures[row->structure_idx]; const Result *r=&results[row->structure_idx];
    csv_field(f,row->baseline_id); fputc(',',f); csv_field(f,s->name); fputc(',',f); csv_field(f,row->deviation); fputc(',',f); csv_field(f,row->term); fputc(',',f); csv_field(f,row->partition);
    fprintf(f,",%u,%u,%u,%s,%d,%d,%s,%.17g,%.17g,%s,%d",r->needed_count,r->relation_count,r->broken,r->broken?"True":"False",r->base_top,r->compound_top,r->compound_top==r->base_top?"True":"False",r->break_fraction,r->closure_load,r->tier,r->tier_order);
    if(ranked) fprintf(f,",%u",rank);
    fputc('\n',f);
}

static int mkdir_p(const char *p){ if(mkdir(p,0775)==0||errno==EEXIST)return 0; return -1; }
static double elapsed_ms(struct timespec a,struct timespec b){ return (b.tv_sec-a.tv_sec)*1000.0+(b.tv_nsec-a.tv_nsec)/1e6; }

static void default_lock_path(const char *argv0,char out[PATH_MAX]){
    char tmp[PATH_MAX];
    strncpy(tmp,argv0,sizeof(tmp)-1); tmp[sizeof(tmp)-1]=0;
    char *slash=strrchr(tmp,'/');
    if(slash) *slash=0; else strcpy(tmp,".");
    snprintf(out,PATH_MAX,"%s/../data/prescreen.lock",tmp);
}

int main(int argc,char **argv){
    if(argc<3||argc>5){ fprintf(stderr,"Usage: %s <compound_formulation> <dose> [output_dir] [lock_file]\n",argv[0]); return 1; }
    const char *compound=argv[1], *dose=argv[2], *outdir=argc>=4?argv[3]:"output"; char lockbuf[PATH_MAX]; default_lock_path(argv[0],lockbuf); const char *lockpath=argc>=5?argv[4]:lockbuf;
    if(!*compound||!*dose) die("compound formulation and dose are required");
    if(mkdir_p(outdir)) die_errno("cannot create output directory");
    struct timespec t0,t1,t2; clock_gettime(CLOCK_MONOTONIC,&t0); LockData d=load_lock(lockpath); clock_gettime(CLOCK_MONOTONIC,&t1);
    size_t qn=strlen(compound)+24; char *q=(char*)malloc(qn); if(!q)die("out of memory"); snprintf(q,qn,"COMPOUND_FORMULATION:%s",compound); double Q[DIMS]; surface_signature((const uint8_t*)q,strlen(q),Q); free(q);
    double molecular_weight=0.0,dose_mg=0.0; double loading=compound_loading_mmol(compound,dose,&molecular_weight,&dose_mg);
    if(loading<0.0) die("dose must be a nonnegative mass (mg/g/ug/mcg/ng) and compound must be a parseable molecular formula");
    Result *results=(Result*)calloc(d.structure_count,sizeof(Result)); if(!results)die("out of memory"); for(uint32_t i=0;i<d.structure_count;i++) results[i]=resolve_structure(&d,&d.structures[i],Q,loading);
    uint32_t tier_counts[5]={0},hit_rows=0; for(uint32_t i=0;i<d.row_count;i++){ Result *r=&results[d.rows[i].structure_idx]; tier_counts[r->tier_order]++; if(r->broken)hit_rows++; }
    uint32_t *hits=(uint32_t*)malloc((size_t)hit_rows*sizeof(uint32_t)); if(!hits)die("out of memory"); uint32_t hp=0; for(uint32_t i=0;i<d.row_count;i++) if(results[d.rows[i].structure_idx].broken) hits[hp++]=i;
    cmp_d=&d; cmp_res=results; qsort(hits,hit_rows,sizeof(uint32_t),hit_cmp);
    char path[PATH_MAX]; snprintf(path,sizeof(path),"%s/results_all_5734.csv",outdir); FILE *fa=fopen(path,"wb"); if(!fa)die_errno("cannot write all results"); write_header(fa,0); for(uint32_t i=0;i<d.row_count;i++) write_row(fa,&d,results,i,0,0); fclose(fa);
    snprintf(path,sizeof(path),"%s/hits_tiered.csv",outdir); FILE *fh=fopen(path,"wb"); if(!fh)die_errno("cannot write hit results"); write_header(fh,1); for(uint32_t i=0;i<hit_rows;i++) write_row(fh,&d,results,hits[i],1,i+1); fclose(fh);
    clock_gettime(CLOCK_MONOTONIC,&t2);
    snprintf(path,sizeof(path),"%s/summary.json",outdir); FILE *fs=fopen(path,"wb"); if(!fs)die_errno("cannot write summary");
    fprintf(fs,"{\n  \"engine\": \"SIDER_Prescreen_C\",\n  \"lock_format\": \"SIDER_PRESCREEN_C_LOCK/1\",\n  \"compound_formulation\": \""); for(const char *p=compound;*p;p++){ if(*p=='"'||*p=='\\')fputc('\\',fs); fputc(*p,fs);} fprintf(fs,"\",\n  \"dose\": \""); for(const char *p=dose;*p;p++){ if(*p=='"'||*p=='\\')fputc('\\',fs); fputc(*p,fs);} fprintf(fs,"\",\n  \"dose_mg\": %.17g,\n  \"molecular_weight_g_mol\": %.17g,\n  \"compound_loading_mmol\": %.17g,\n  \"dose_model\": \"compound identity fixed; perturbation scaled continuously by mmol = dose_mg / molecular_weight_g_mol\",\n  \"matrix_rows\": %u,\n  \"unique_structures\": %u,\n  \"hit_rows\": %u,\n  \"tier_counts\": {\"NONE\": %u, \"LOW\": %u, \"MEDIUM\": %u, \"HIGH\": %u, \"CRITICAL\": %u},\n  \"cache_load_ms\": %.3f,\n  \"resolve_and_write_ms\": %.3f,\n  \"tier_rule\": \"NONE b=0; LOW 0<b/r<=0.25; MEDIUM 0.25<b/r<=0.50; HIGH 0.50<b/r<1; CRITICAL b/r=1\",\n  \"closure_load_formula\": \"(broken/total)*ln(1+total)\"\n}\n",dose_mg,molecular_weight,loading,d.row_count,d.structure_count,hit_rows,tier_counts[0],tier_counts[1],tier_counts[2],tier_counts[3],tier_counts[4],elapsed_ms(t0,t1),elapsed_ms(t1,t2)); fclose(fs);
    printf("SIDER_Prescreen_C: %u rows, %u hits | NONE=%u LOW=%u MEDIUM=%u HIGH=%u CRITICAL=%u | %.3f ms total\n",d.row_count,hit_rows,tier_counts[0],tier_counts[1],tier_counts[2],tier_counts[3],tier_counts[4],elapsed_ms(t0,t2));
    free(hits); free(results); free_lock(&d); return 0;
}
