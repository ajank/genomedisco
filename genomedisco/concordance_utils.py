from __future__ import print_function
import argparse
import os
import re
import subprocess as subp
import gzip
import numpy as np
from time import gmtime, strftime
import sys
import copy
import fnmatch

global repo_dir
global replicateqc_path
global python_bin_dir
repo_dir=os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
replicateqc_path=os.path.dirname(os.path.dirname(repo_dir))
python_bin_dir=os.path.dirname(sys.executable)
bashrc_file=replicateqc_path+'/configuration_files/bashrc.configuration'

def parse_args_genomedisco():
    return parse_args('GenomeDISCO')

def parse_args_replicateqc():
    return parse_args('replicateqc')

def parse_args(genomedisco_or_replicateqc):
    parser = argparse.ArgumentParser(description='')

    #individual parsers
    metadata_samples_parser=argparse.ArgumentParser(add_help=False)
    metadata_samples_parser.add_argument('--metadata_samples',required=True,help='required. A file where each row represents a sample, and the entries are "samplename samplefile". Each of these will be processed. Note: each samplename in the file MUST be unique. Each samplefile listed here should follow the format "chr1 bin1 chr2 bin2 value"')

    metadata_pairs_parser=argparse.ArgumentParser(add_help=False)
    metadata_pairs_parser.add_argument('--metadata_pairs',required=True,help='required. Each row is a pair of sample names to be compared, in the format "samplename1 samplename2". Important: sample names used here need to correspond to the first column of the --metadata_samples file.')

    bins_parser=argparse.ArgumentParser(add_help=False)
    bins_parser.add_argument('--bins',required=True,help='required. A (gzipped) bed file of the all bins used in the analysis. It should have 4 columns: "chr start end name", where the name of the bin corresponds to the bins used in the contact maps.')

    re_fragments_parser=argparse.ArgumentParser(add_help=False)
    re_fragments_parser.add_argument('--re_fragments',action='store_true',help='Add this flag if the bins are not uniform bins in the genome (e.g. if they are restriction-fragment-based). By default, the code assumes the bins are of uniform length.')

    outdir_parser=argparse.ArgumentParser(add_help=False)
    outdir_parser.add_argument('--outdir',default='replicateQC',help='Name of output directory. DEFAULT: replicateQC')
    
    parameter_file_parser=argparse.ArgumentParser(add_help=False)
    parameter_file_parser.add_argument('--parameters_file',help='File with parameters for reproducibility and QC analysis. See the documentation for details.',default='NA')

    concise_analysis_parser=argparse.ArgumentParser(add_help=False)
    concise_analysis_parser.add_argument('--concise_analysis',action='store_true',help='Set this flag to obtain a concise analysis, which means replicateQC is measured but plots that might be more time/memory consuming are not created.')

    running_mode_parser=argparse.ArgumentParser(add_help=False)
    running_mode_parser.add_argument('--running_mode',default='NA',help='The mode in which to run the analysis. This allows you to choose whether the analysis will be run as is, or submitted as a job through sge or slurm. Available options are: "NA" (default, no jobs are submitted), "sge", "slurm"')

    subset_chromosomes_parser=argparse.ArgumentParser(add_help=False)
    subset_chromosomes_parser.add_argument('--subset_chromosomes',default='NA',help='Comma-delimited list of chromosomes for which you want to run the analysis. By default the analysis runs on all chromosomes for which there are data. This is useful for quick testing')

    timing_parser=argparse.ArgumentParser(add_help=False)
    timing_parser.add_argument('--timing',action='store_true',help='Set this flag to time the analyses. Files detailing the running times of each method can be found in outdir/running_times')

    #TODO: jobs waiting for each other
    if genomedisco_or_replicateqc=='replicateqc':
        methods_parser=argparse.ArgumentParser(add_help=False)
        methods_parser.add_argument('--methods',default='GenomeDISCO,HiCRep,HiC-Spector,QuASAR-QC,QuASAR-Rep',help='Which method to use for measuring concordance or QC. Comma-delimited list. Possible methods: "GenomeDISCO", "HiCRep", "HiC-Spector", "QuASAR-Rep", "QuASAR-QC". By default all methods are run.') 

    if genomedisco_or_replicateqc=='GenomeDISCO':
        methods_parser=argparse.ArgumentParser(add_help=False)
        methods_parser.add_argument('--methods',default='GenomeDISCO',help='Which method to use for measuring concordance. Only GenomeDISCO is supported. For running all methods (including GenomeDISCO), refer to the repository https://github.com/kundajelab/3DChromatin_ReplicateQC')

    subparsers = parser.add_subparsers(help='', dest='command')
    subparsers.required = True #http://bugs.python.org/issue9253#msg186387

    #parsers for commands
    if genomedisco_or_replicateqc=='replicateqc':
        all_parser=subparsers.add_parser('run_all',parents=[metadata_samples_parser,metadata_pairs_parser,bins_parser,re_fragments_parser,methods_parser,parameter_file_parser,outdir_parser,running_mode_parser,concise_analysis_parser,subset_chromosomes_parser,timing_parser],help='Run all steps in the reproducibility/QC analysis with this single command')
    
    if genomedisco_or_replicateqc=='GenomeDISCO':
        all_parser=subparsers.add_parser('run_all',parents=[metadata_samples_parser,metadata_pairs_parser,bins_parser,re_fragments_parser,parameter_file_parser,outdir_parser,running_mode_parser,concise_analysis_parser,subset_chromosomes_parser,timing_parser],help='Run all steps in the concordance analysis with this single command')

    if genomedisco_or_replicateqc=='replicateqc':
        split_parser=subparsers.add_parser('preprocess',parents=[metadata_samples_parser,bins_parser,re_fragments_parser,methods_parser,outdir_parser,running_mode_parser,subset_chromosomes_parser,parameter_file_parser,timing_parser],help='(step 1) split files by chromosome')
    if genomedisco_or_replicateqc=='GenomeDISCO':
        split_parser=subparsers.add_parser('preprocess',parents=[metadata_samples_parser,bins_parser,re_fragments_parser,outdir_parser,running_mode_parser,subset_chromosomes_parser,parameter_file_parser,timing_parser],help='(step 1) split files by chromosome')

    if genomedisco_or_replicateqc=='replicateqc':
        qc_parser=subparsers.add_parser('qc',parents=[metadata_samples_parser,methods_parser,outdir_parser,running_mode_parser,concise_analysis_parser,subset_chromosomes_parser,timing_parser],help='(step 2.a) compute QC per sample')

    if genomedisco_or_replicateqc=='replicateqc':
        reproducibility_parser=subparsers.add_parser('concordance',parents=[metadata_pairs_parser,methods_parser,outdir_parser,running_mode_parser,concise_analysis_parser,subset_chromosomes_parser,timing_parser],help='(step 2.b) compute reproducibility of replicate pairs')

    if genomedisco_or_replicateqc=='GenomeDISCO':
        reproducibility_parser=subparsers.add_parser('concordance',parents=[metadata_pairs_parser,outdir_parser,running_mode_parser,concise_analysis_parser,subset_chromosomes_parser,timing_parser],help='(step 2) compute concordance of replicate pairs')

    if genomedisco_or_replicateqc=='replicateqc':
        summary_parser=subparsers.add_parser('summary',parents=[metadata_samples_parser,metadata_pairs_parser,bins_parser,re_fragments_parser,methods_parser,outdir_parser,running_mode_parser,concise_analysis_parser,subset_chromosomes_parser],help='(step 3) create html report of the results')

    if genomedisco_or_replicateqc=='GenomeDISCO':
        summary_parser=subparsers.add_parser('summary',parents=[metadata_samples_parser,metadata_pairs_parser,bins_parser,re_fragments_parser,outdir_parser,running_mode_parser,concise_analysis_parser,subset_chromosomes_parser],help='(step 3) create html report of the results')

    cleanup_parser=subparsers.add_parser('cleanup',parents=[outdir_parser],help='(step 4) clean up files')

    args = vars(parser.parse_args())
    command = args.pop("command", None)
    return command, args

def write_resolution(nodes,resolution_filename):
    resolution_file=open(resolution_filename,'w')
    node_sizes=[]
    for line in gzip.open(nodes,'r'):
        items=line.strip().split('\t')
        chromo,start,end,name=items[0],items[1],items[2],items[3]
        node_sizes.append(int(end)-int(start))
    resolution=int(np.median(np.array(node_sizes)))
    resolution_file.write(str(resolution)+'\n')

def preprocess(metadata_samples,bins,re_fragments,methods,outdir,running_mode,subset_chromosomes,parameters_file,timing):
    methods_list=methods.split(',')

    #change paths to absolute paths
    nodes=os.path.abspath(bins)
    outdir=os.path.abspath(outdir)
    metadata_samples=os.path.abspath(metadata_samples)
    if parameters_file=='NA':
        parameters_file=os.path.dirname(os.path.realpath(__file__))+"/example_parameters.txt"

    #==================================
    # setting up the analysis directory
    #==================================
    #make the directory structure for the reproducibility analysis
    subp.check_output(['bash','-c','mkdir -p '+outdir+'/scripts'])
    subp.check_output(['bash','-c','mkdir -p '+outdir+'/data/metadata'])
    subp.check_output(['bash','-c','mkdir -p '+outdir+'/data/edges'])
    subp.check_output(['bash','-c','mkdir -p '+outdir+'/data/nodes'])
    subp.check_output(['bash','-c','mkdir -p '+outdir+'/results'])
    #make a copy of the parameters for the analysis - after this, the parameters will be read from the copy
    subp.check_output(['bash','-c','cp '+parameters_file+' '+outdir+'/parameters.txt'])

    #========================================
    # get chromosomes, resolution, parameters
    #========================================
    #make a list of all the chromosomes in the nodes file
    subp.check_output(['bash','-c','gunzip -c '+nodes+' | cut -f1 | sort | uniq | awk \'{print "chr"$0}\' | sed \'s/chrchr/chr/g\' | gzip > '+outdir+'/data/metadata/chromosomes.gz'])
    #figure out resolution here and use it in the other steps
    resolution_file=outdir+'/data/metadata/resolution.txt'
    write_resolution(nodes,resolution_file)
    resolution=open(resolution_file,'r').readlines()[0].split()[0]
    parameters=read_parameters_file(parameters_file)

    #========================================
    # Pre-process data for QuASAR
    #========================================
    if 'QuASAR-QC' in methods_list or 'QuASAR-Rep' in methods_list or "all" in methods_list:
        quasar_preprocess(metadata_samples,outdir,subset_chromosomes,running_mode,timing,parameters,resolution,nodes)

    #========================================
    # Pre-process data for the other methods
    #========================================
    if 'GenomeDISCO' in methods_list or 'HiCRep' in methods_list or 'HiC-Spector' in methods_list or "all" in methods_list:
        nonquasar_preprocess(metadata_samples,outdir,subset_chromosomes,running_mode,timing,parameters,nodes)

def nonquasar_preprocess(metadata_samples,outdir,subset_chromosomes,running_mode,timing,parameters,nodes):

        #split the data into chromosomes
        for chromo_line in gzip.open(outdir+'/data/metadata/chromosomes.gz','r').readlines():
            chromo=chromo_line.strip()
            if subset_chromosomes!='NA':
                if chromo not in subset_chromosomes.split(','):
                    continue
            #nodes ===============
            script_nodes_file=outdir+'/scripts/split/nodes/'+chromo+'.nodes.split_files_by_chromosome.sh'
            subp.check_output(['bash','-c','mkdir -p '+os.path.dirname(script_nodes_file)])
            script_nodes=open(script_nodes_file,'w')
            script_nodes.write("#!/bin/sh"+'\n')
            nodefile=outdir+'/data/nodes/nodes.'+chromo+'.gz'

            print('Step: preprocess | '+strftime("%c")+' | Splitting nodes '+chromo)

            script_nodes.write("gunzip -c "+nodes+' | sort -k1,1 -k2,2n | awk \'{print "chr"$1"\\t"$2"\\t"$3"\\t"$4"\\tincluded"}\' | sed \'s/chrchr/chr/g\' | awk -v chromosome='+chromo+' \'{if ($1==chromosome) print $0}\' | gzip > '+nodefile+'\n')
            script_nodes.write('rm '+script_nodes_file+'*'+'\n')
            script_nodes.close()
            run_script(script_nodes_file,running_mode,parameters)

            #edges =====================
            for line in open(metadata_samples,'r').readlines():
                items=line.strip().split()
                samplename=items[0]
                
                print('Step: preprocess | '+strftime("%c")+' | Splitting '+samplename+' '+chromo)

                samplefile=items[1]
                script_edges_file=outdir+'/scripts/split/'+samplename+'/'+chromo+'.'+samplename+'.split_files_by_chromosome.sh'
                subp.check_output(['bash','-c','mkdir -p '+os.path.dirname(script_edges_file)])
                script_edges=open(script_edges_file,'w')
                script_edges.write("#!/bin/sh"+'\n')
                edgefile=outdir+'/data/edges/'+samplename+'/'+samplename+'.'+chromo+'.gz'
                script_edges.write('mkdir -p '+os.path.dirname(edgefile)+'\n')
                script_edges.write('gunzip -c '+samplefile+' | awk \'{print "chr"$1"\\t"$2"\\tchr"$3"\\t"$4"\\t"$5}\' | sed \'s/chrchr/chr/g\' | awk -v chromosome='+chromo+' \'{if ($1==chromosome && $3==chromosome) print $2"\\t"$4"\\t"$5}\' | gzip > '+edgefile+'\n')
                #write down total counts per chromosome
                script_edges.write('gunzip -c '+edgefile+' | awk \'{ sum += $3} END { print sum }\' > '+outdir+'/data/edges/'+samplename+'/'+samplename+'.'+chromo+'.counts'+'\n') 
                script_edges.write('rm '+script_edges_file+'*'+'\n')
                script_edges.close()
                run_script(script_edges_file,running_mode,parameters)

    #for genomedisco, we need to get the 

def quasar_preprocess(metadata_samples,outdir,subset_chromosomes,running_mode,timing,parameters,resolution,nodes):
    #setup parameters
    rebinning=parameters['QuASAR']['rebinning']
    if rebinning=='resolution':
        rebinning=resolution

    #make partition = nodes for QuASAR
    quasar_data=outdir+'/data/forQuASAR'
    subp.check_output(['bash','-c','mkdir -p '+quasar_data])
    nodes_partition=quasar_data+'/nodes.partition'
    script_forquasar_file=outdir+'/scripts/forQuASAR/QuASARmakeData.sh'
    subp.check_output(['bash','-c','mkdir -p '+os.path.dirname(script_forquasar_file)])
    script_forquasar=open(script_forquasar_file,'w')
    script_forquasar.write("#!/bin/sh"+'\n')
    script_forquasar.write(sys.executable+' '+replicateqc_path+"/wrappers/QuASAR/make_partition_from_bedfile.py --nodes "+nodes+' --partition '+nodes_partition+' --subset_chromosomes '+subset_chromosomes+' --resolution '+resolution+'\n')
    

    #go through each sample, and process it for QuASAR
    for line in open(metadata_samples,'r').readlines():
        items=line.strip().split()
        samplename=items[0]
        samplefile=items[1]
        full_dataset=quasar_data+'/'+samplename+'.fulldata.gz'
        quasar_output=quasar_data+'/'+samplename+'.quasar_data'
        quasar_project=quasar_data+'/'+samplename+'.quasar_project'
        quasar_transform=quasar_data+'/'+samplename+'.quasar_transform'
        if subset_chromosomes=='NA':
            #all chromosomes                                                                                
            script_forquasar.write('gunzip -c  '+samplefile+' | sed \'s/chr//g\' | awk \'{print "chr"$1"'+'\\'+'t'+'"$2"\\tchr"$3"\\t"$4"\\t"$5}\' | gzip > '+full_dataset+'\n')
        else:
            script_forquasar.write('if [ ! '+full_dataset+'.tmp ];then rm '+full_dataset+'.tmp;fi'+'\n')
            for chromosome in subset_chromosomes.split(','):
                #TODO: keep inter-chromosomals                                                              
                script_forquasar.write('gunzip -c  '+samplefile+' | awk \'{print "chr"$1"\\t"$2"\\tchr"$3"\\t"$4"\\t"$5}\' | sed \'s/chrchr/chr/g\' | awk -v chromo='+chromosome+' \'{if (($1==$3) && ($1==chromo)) print $0}\' >> '+full_dataset+'.tmp'+'\n')
            script_forquasar.write('gzip '+full_dataset+'.tmp'+'\n')
            script_forquasar.write('gunzip -c  '+full_dataset+'.tmp.gz | gzip > '+full_dataset+'\n')
            script_forquasar.write('rm '+full_dataset+'.tmp'+'\n')

        #make quasar dataset
        script_forquasar.write(sys.executable+' '+replicateqc_path+"/wrappers/QuASAR/data_to_hifive.py "+full_dataset+" "+nodes_partition+' '+quasar_output+'\n')
        script_forquasar.write('rm '+full_dataset+'\n')
        
        #make project
        script_forquasar.write(sys.executable+' -c "import hifive; hic=hifive.HiC(\''+quasar_project+'\',\'w\'); hic.load_data(\''+quasar_output+'\'); hic.save()"'+'\n')

        #quasar tranformation        
        script_forquasar.write(python_bin_dir+'/hifive quasar -p '+quasar_project+' '+quasar_transform+' -r '+rebinning+' -d 0'+'\n')

        #remove intermediate files
        script_forquasar.write('rm '+quasar_output+' '+quasar_project+'\n')
    script_forquasar.close()
    run_script(script_forquasar_file,running_mode,parameters)

def run_script(script_name,running_mode,parameters):

    subp.check_output(['bash','-c','chmod 755 '+script_name])
    if running_mode=='NA':
        #print script_name+'.timed'
        output=subp.check_output(['bash','-c',script_name])
        #output=subp.check_output(['bash','-c','{ time '+script_name+'; } 2> '+script_name+'.timed'])
        if output!='':
            print(output)
    if running_mode=='write_script':
        pass
    if running_mode=='sge':
        output=subp.check_output(['bash','-c','qsub '+re.sub('"','',parameters['SGE']['text'])+' -o '+script_name+'.o -e '+script_name+'.e '+script_name])
        #print 'qsub '+re.sub('"','',parameters['SGE']['text'])+' -o '+script_name+'.o -e '+script_name+'.e '+script_name
        print(output)
    if running_mode=='slurm':
        output=subp.check_output(['bash','-c','sbatch '+re.sub('"','',parameters['slurm']['text'])+' -o '+script_name+'.o -e '+script_name+'.e'+' '+script_name])
        print(output)

def read_parameters_file(parameters_file):
    parameters={}
    for line in open(parameters_file,'r').readlines():
        items=re.sub('\|','\t',line).strip().split('\t')
        method_name,param_name,param_value=items[0],items[1],items[2]
        if method_name not in parameters:
            parameters[method_name]={}
        parameters[method_name][param_name]=param_value
    return parameters

def QuASAR_rep_wrapper(outdir,parameters,samplename1,samplename2,running_mode,timing):
    script_comparison_file=outdir+'/scripts/QuASAR-Rep/'+samplename1+'.vs.'+samplename2+'/'+samplename1+'.vs.'+samplename2+'.QuASAR-Rep.sh'
    subp.check_output(['bash','-c','mkdir -p '+os.path.dirname(script_comparison_file)])
    script_comparison=open(script_comparison_file,'w')
    script_comparison.write("#!/bin/sh"+'\n')
    outpath=outdir+'/results/reproducibility/QuASAR-Rep/'+samplename1+'.vs.'+samplename2+'.QuASAR-Rep.scores.txt'
    subp.check_output(['bash','-c','mkdir -p '+os.path.dirname(outpath)])
    quasar_data=outdir+'/data/forQuASAR'
    quasar_transform1=quasar_data+'/'+samplename1+'.quasar_transform'
    quasar_transform2=quasar_data+'/'+samplename2+'.quasar_transform'
    timing_text1=''
    timing_text2=''
    if timing:
        subp.check_output(['bash','-c','mkdir -p '+outdir+'/timing/QuASAR-Rep'])
        timing_file=outdir+'/timing/QuASAR-Rep/QuASAR-Rep.'+samplename1+'.'+samplename2+'.timing.txt'
        timing_text1='{ time '
        timing_text2='; } 2> '+timing_file
    script_comparison.write(timing_text1+python_bin_dir+"/hifive quasar"+' -Q '+quasar_transform2+' -o '+outpath+' -d 0'+' '+quasar_transform1+timing_text2+'\n') 
    #script_comparison.write('${mypython} '+repo_dir+"/wrappers/QuASAR/plot_quasar_scatter.py"+' '+quasar_transform1+' '+quasar_transform2+' '+outpath+'\n')
    #split the scores by chromosomes
    script_comparison.write('sleep 10'+'\n')
    script_comparison.write(sys.executable+' '+replicateqc_path+"/wrappers/QuASAR/quasar_combine_by_chromosomes.py"+' '+outpath+' '+samplename1+' '+samplename2+'\n')
    script_comparison.write('rm '+outpath+'\n')
    script_comparison.close()
    run_script(script_comparison_file,running_mode,parameters)

def quasar_qc_wrapper(outdir,parameters,samplename,running_mode,timing):
    script_comparison_file=outdir+'/scripts/QuASAR-QC/'+samplename+'/'+samplename+'.QuASAR-QC.sh'
    subp.check_output(['bash','-c','mkdir -p '+os.path.dirname(script_comparison_file)])
    script_comparison=open(script_comparison_file,'w')
    script_comparison.write("#!/bin/sh"+'\n')
    outpath=outdir+'/results/qc/'+samplename+'/QuASAR-QC/'+samplename+'.QuASAR-QC.scores.txt'
    quasar_data=outdir+'/data/forQuASAR'
    quasar_transform=quasar_data+'/'+samplename+'.quasar_transform'
    subp.check_output(['bash','-c','mkdir -p '+os.path.dirname(outpath)])
    timing_text1=''
    timing_text2=''
    if timing:
        subp.check_output(['bash','-c','mkdir -p '+outdir+'/timing/QuASAR-QC'])
        timing_file=outdir+'/timing/QuASAR-QC/QuASAR-QC.'+samplename+'.timing.txt'
        timing_text1='{ time '
        timing_text2='; } 2> '+timing_file
    script_comparison.write(timing_text1+python_bin_dir+"/hifive quasar"+' '+quasar_transform+' -o '+outpath+' '+timing_text2+'\n')
    script_comparison.write(sys.executable+' '+replicateqc_path+"/wrappers/QuASAR/quasar_split_by_chromosomes_qc.py"+' '+outpath+' '+samplename+'\n')
    script_comparison.close()
    run_script(script_comparison_file,running_mode,parameters)

def HiCRep_wrapper(outdir,parameters,concise_analysis,samplename1,samplename2,chromo,running_mode,f1,f2,nodefile,resolution,all_scores,timing):
    cmdlist=[]
    cmdlist.append("#!/bin/sh")
    cmdlist.append('. '+bashrc_file)
    if os.path.isfile(f1) and os.path.getsize(f1)>20:
        if os.path.isfile(f2) and os.path.getsize(f2)>20:
            outpath=outdir+'/results/reproducibility/HiCRep/'+chromo+'.'+samplename1+'.vs.'+samplename2+'.scores.txt'
            subp.check_output(['bash','-c','mkdir -p '+os.path.dirname(outpath)])
            hicrepcode=replicateqc_path+"/wrappers/HiCRep/HiCRep_wrapper.R"
            timing_text1=''
            timing_text2=''
            if timing:
                cmdlist.append('mkdir -p '+outdir+'/timing/HiCRep')
                timing_file=outdir+'/timing/HiCRep/HiCRep.'+chromo+'.'+samplename1+'.'+samplename2+'.timing.txt'
                timing_text1='{ time '
                timing_text2='; } 2> '+timing_file
            cmd=timing_text1+"${pathtor}script "+hicrepcode+' '+f1+' '+f2+' '+outpath+' '+parameters['HiCRep']['maxdist']+' '+str(resolution)+' '+nodefile+' '+parameters['HiCRep']['h']+' '+samplename1+' '+samplename2+' '+timing_text2
            cmdlist.append(cmd)
            cmdlist.append('cat '+outpath+" | awk -v chromosome="+chromo+" '{print "+'$1"\\t"$2"\\t"chromosome"\\t"$3}\' >> '+all_scores)
    return cmdlist
    
def HiCSpector_wrapper(outdir,parameters,concise_analysis,samplename1,samplename2,chromo,running_mode,f1,f2,nodefile,all_scores,timing,resolution):
    cmdlist=[]
    cmdlist.append("#!/bin/sh")
    if os.path.isfile(f1) and os.path.getsize(f1)>20:
        if os.path.isfile(f2) and os.path.getsize(f2)>20:
            outpath=outdir+'/results/reproducibility/HiC-Spector/'+chromo+'.'+samplename1+'.vs.'+samplename2+'.scores.txt'
            subp.check_output(['bash','-c','mkdir -p '+os.path.dirname(outpath)])
            timing_text1=''
            timing_text2=''
            if timing:
                cmdlist.append('mkdir -p '+outdir+'/timing/HiC-Spector')
                timing_file=outdir+'/timing/HiC-Spector/HiC-Spector.'+chromo+'.'+samplename1+'.'+samplename2+'.timing.txt'
                timing_text1='{ time '
                timing_text2='; } 2> '+timing_file
            #cmdlist.append(timing_text1+sys.executable+" -W ignore "+replicateqc_path+"/wrappers/HiC-Spector/hic-spector_wrapper.py --m1 "+f1+" --m2 "+f2+" --out "+outpath+".printout --node_file "+nodefile+" --num_evec "+parameters['HiC-Spector']['n']+' '+timing_text2)
            #cmdlist.append("cat "+outpath+".printout | grep reproducibility | cut -f2 | awk '{print \""+samplename1+"\\t"+samplename2+"\\t\"$3}' > "+outpath)
            #cmdlist.append("rm "+outpath+".printout")
            #cmdlist.append('cat '+outpath+" | awk -v chromosome="+chromo+" '{print "+'$1"\\t"$2"\\t"chromosome"\\t"$3}\' >> '+all_scores)
            cmdlist.append(timing_text1+sys.executable+" -W ignore "+replicateqc_path+"/wrappers/HiC-Spector/run_reproducibility_v1.py t "+f1+" "+f2+" "+outpath+".printout "+str(resolution)+" "+parameters['HiC-Spector']['n']+' '+timing_text2)
            cmdlist.append("cat "+outpath+".printout | tail -n1 | cut -f2 | awk '{print \""+samplename1+"\\t"+samplename2+"\\t\"$3}' > "+outpath)
            cmdlist.append("rm "+outpath+".printout")
            cmdlist.append('cat '+outpath+" | awk -v chromosome="+chromo+" '{print "+'$1"\\t"$2"\\t"chromosome"\\t"$3}\' >> '+all_scores)
    return cmdlist
        
def GenomeDISCO_wrapper(outdir,parameters,concise_analysis,samplename1,samplename2,chromo,running_mode,f1,f2,nodefile,all_scores,timing):

    cmdlist=[]
    cmdlist.append("#!/bin/sh")
    if os.path.isfile(f1) and os.path.getsize(f1)>20:                                                 
        if os.path.isfile(f2) and os.path.getsize(f2)>20:                                             
            concise_analysis_text=''                                                                  
            if concise_analysis:                                                                      
                concise_analysis_text=' --concise_analysis'              
            scoresByStep_text=''
            if parameters['GenomeDISCO']['scoresByStep']=='yes':
                scoresByStep_text=' --scoresByStep'
            removeDiag_text=''
            if parameters['GenomeDISCO']['removeDiag']=='yes':
                removeDiag_text=' --remove_diagonal'
            transition_text=''
            if parameters['GenomeDISCO']['transition']=='yes':
                transition_text=' --transition'
            #get the sample that goes for subsampling
            subsampling=parameters['GenomeDISCO']['subsampling']
            if parameters['GenomeDISCO']['subsampling']!='NA' and parameters['GenomeDISCO']['subsampling']!='lowest':
                subsampling_sample=parameters['GenomeDISCO']['subsampling']
                subsampling=outdir+'/data/edges/'+subsampling_sample+'/'+subsampling_sample+'.'+chromo+'.gz'

            outpath=outdir+'/results/reproducibility/GenomeDISCO'
            cmdlist.append('mkdir -p '+outpath)
            #{ time ./testscript.sh; } 2> out.txt
            timing_text1=''
            timing_text2=''
            cmdlist.append('cd '+os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
            
            if timing:
                cmdlist.append('mkdir -p '+outdir+'/timing/GenomeDISCO')
                timing_file=outdir+'/timing/GenomeDISCO/GenomeDISCO.'+chromo+'.'+samplename1+'.'+samplename2+'.timing.txt'
                timing_text1='{ time '
                timing_text2='; } 2> '+timing_file
            cmd=timing_text1+sys.executable+" "+repo_dir+"/genomedisco/compute_reproducibility.py"+" --m1 "+f1+" --m2 "+f2+" --m1name "+samplename1+" --m2name "+samplename2+" --node_file "+nodefile+" --outdir "+outpath+" --outpref "+chromo+" --subsampling_depth "+subsampling+" --approximation 10000000 --norm "+parameters['GenomeDISCO']['norm']+" --method RandomWalks "+" --tmin "+parameters['GenomeDISCO']['tmin']+" --tmax "+parameters['GenomeDISCO']['tmax']+concise_analysis_text+scoresByStep_text+removeDiag_text+transition_text+' '+timing_text2
            cmdlist.append(cmd)
            cmdlist.append('cat '+outpath+'/'+chromo+'.'+samplename1+'.vs.'+samplename2+".scores.txt | awk -v chromosome="+chromo+" '{print "+'$1"\\t"$2"\\t"chromosome"\\t"$3}\' >> '+all_scores)
    return cmdlist

def add_cmds_to_file(cmds,cmds_filename):
    if os.path.exists(cmds_filename):
        cmds_file=open(cmds_filename,'a')
    else:
        cmds_file=open(cmds_filename,'w')
    for i in range(len(cmds)):
        cmds_file.write(cmds[i]+'\n')
    cmds_file.close()

def concordance(metadata_pairs,methods,outdir,running_mode,concise_analysis,subset_chromosomes,timing):
    #todo: remove parameters file from the arguments here
    parameters_file=outdir+'/parameters.txt'

    #remove scripts from splits
    scripts_from_split=outdir+'/scripts/split'
    if os.path.exists(scripts_from_split):
        subp.check_output(['bash','-c','rm -r '+scripts_from_split])

    methods_list=methods.split(',')
    parameters=read_parameters_file(parameters_file)

    outdir=os.path.abspath(outdir)
    metadata_pairs=os.path.abspath(metadata_pairs)

    resolution_file=outdir+'/data/metadata/resolution.txt'
    resolution=open(resolution_file,'r').readlines()[0].split()[0]

    scripts_to_run=set()

    for line in open(metadata_pairs,'r').readlines():                                                     
        items=line.strip().split()                                                                       
        samplename1,samplename2=items[0],items[1]
        print('Step: concordance | '+strftime("%c")+' | '+'computing concordance between '+samplename1+' and '+samplename2)

        #total scores per sample
        GenomeDISCO_scores=outdir+'/results/reproducibility/GenomeDISCO/'+samplename1+'.vs.'+samplename2+'.txt'
        HiCRep_scores=outdir+'/results/reproducibility/HiCRep/'+samplename1+'.vs.'+samplename2+'.txt'
        HiCSpector_scores=outdir+'/results/reproducibility/HiC-Spector/'+samplename1+'.vs.'+samplename2+'.txt'

        #scripts for each method
        cmds_file={}
        for method in ['GenomeDISCO','HiCRep','HiC-Spector']:
            cmds_file[method]=outdir+'/scripts/'+method+'/'+samplename1+'.'+samplename2+'.sh'
            if method in methods_list or "all" in methods_list:
                if os.path.exists(cmds_file[method]):
                    subp.check_output(['bash','-c','rm '+cmds_file[method]])

        if os.path.exists(GenomeDISCO_scores):
            if "GenomeDISCO" in methods_list or "all" in methods_list:
                subp.check_output(['bash','-c','rm '+GenomeDISCO_scores])
        if os.path.exists(HiCRep_scores):
            if "HiCRep" in methods_list or "all" in methods_list:
                subp.check_output(['bash','-c','rm '+HiCRep_scores])
        if os.path.exists(HiCSpector_scores):
            if "HiC-Spector" in methods_list or "all" in methods_list:
                subp.check_output(['bash','-c','rm '+HiCSpector_scores])

        #scripts
        for method in ['GenomeDISCO','HiCRep','HiC-Spector','QuASAR-Rep','QuASAR-QC']:
            if not os.path.exists(outdir+'/scripts/'+method):
                subp.check_output(['bash','-c','mkdir -p '+outdir+'/scripts/'+method])

        if "QuASAR-Rep" in methods_list or "all" in methods_list:
            QuASAR_rep_wrapper(outdir,parameters,samplename1,samplename2,running_mode,timing)

        for chromo_line in gzip.open(outdir+'/data/metadata/chromosomes.gz','r').readlines():               
            chromo=chromo_line.strip()
            if subset_chromosomes!='NA':
                if chromo not in subset_chromosomes.split(','):
                    continue

            f1=outdir+'/data/edges/'+samplename1+'/'+samplename1+'.'+chromo+'.gz'
            f2=outdir+'/data/edges/'+samplename2+'/'+samplename2+'.'+chromo+'.gz'
            nodefile=outdir+'/data/nodes/nodes.'+chromo+'.gz'

            if "GenomeDISCO" in methods_list or "all" in methods_list:
                scripts_to_run.add(cmds_file['GenomeDISCO'])
                GenomeDISCO_cmds=GenomeDISCO_wrapper(outdir,parameters,concise_analysis,samplename1,samplename2,chromo,running_mode,f1,f2,nodefile,GenomeDISCO_scores,timing)
                add_cmds_to_file(GenomeDISCO_cmds,cmds_file['GenomeDISCO'])           
                

            if "HiCRep" in methods_list or "all" in methods_list:
                scripts_to_run.add(cmds_file['HiCRep'])
                HiCRep_cmds=HiCRep_wrapper(outdir,parameters,concise_analysis,samplename1,samplename2,chromo,running_mode,f1,f2,nodefile,resolution,HiCRep_scores,timing)
                add_cmds_to_file(HiCRep_cmds,cmds_file['HiCRep'])

            if "HiC-Spector" in methods_list or "all" in methods_list:
                scripts_to_run.add(cmds_file['HiC-Spector'])
                HiCSpector_cmds=HiCSpector_wrapper(outdir,parameters,concise_analysis,samplename1,samplename2,chromo,running_mode,f1,f2,nodefile,HiCSpector_scores,timing,resolution)
                add_cmds_to_file(HiCSpector_cmds,cmds_file['HiC-Spector'])

        #remove files with scores for individual chromosomes
        for chromo_line in gzip.open(outdir+'/data/metadata/chromosomes.gz','r').readlines():
            chromo=chromo_line.strip()
            if subset_chromosomes!='NA':
                if chromo not in subset_chromosomes.split(','):
                    continue
            if "GenomeDISCO" in methods_list or "all" in methods_list:
                thefile=outdir+'/results/reproducibility/GenomeDISCO/'+chromo+'.'+samplename1+'.vs.'+samplename2+'.scores.txt'
                add_cmds_to_file(['if [ -f '+thefile+' ] ; then rm '+thefile+';fi'],cmds_file['GenomeDISCO'])
            if "HiCRep" in methods_list or "all" in methods_list:
                thefile=outdir+'/results/reproducibility/HiCRep/'+chromo+'.'+samplename1+'.vs.'+samplename2+'.scores.txt'
                add_cmds_to_file(['if [ -f '+thefile+' ] ; then rm '+thefile+';fi'],cmds_file['HiCRep'])
            if "HiC-Spector" in methods_list or "all" in methods_list:
                thefile=outdir+'/results/reproducibility/HiC-Spector/'+chromo+'.'+samplename1+'.vs.'+samplename2+'.scores.txt'
                add_cmds_to_file(['if [ -f '+thefile+' ] ; then rm '+thefile+';fi'],cmds_file['HiC-Spector'])

    #run scripts ==========================
    scripts_to_run=list(scripts_to_run)
    scripts_to_run.sort()
    for f in scripts_to_run:
        #add_cmds_to_file(['rm '+f],f)
        run_script(f,running_mode,parameters)

def get_qc(metadata_samples,methods,outdir,running_mode,concise_analysis,subset_chromosomes,timing):
    parameters_file=outdir+'/parameters.txt'
    parameters=read_parameters_file(parameters_file)
    methods_list=methods.strip().split(',')
    if 'QuASAR-QC' in methods_list or 'all' in methods_list:
        #TODO: have fewer parameters for this function
        for line in open(metadata_samples,'r').readlines():
            items=line.strip().split()
            samplename=items[0]
            samplefile=items[1]
            print('Step: qc | '+strftime("%c")+' | '+'running QuASAR-QC | computing QC for '+samplename)
            quasar_qc_wrapper(outdir,parameters,samplename,running_mode,timing)

def summary(metadata_samples,metadata_pairs,bins,re_fragments,methods,outdir,running_mode,concise_analysis,subset_chromosomes):
    methods_list=methods.split(',')

    print('Step: summary | '+strftime("%c"))
    #compile scores across methods per chromosome, + genomewide                                            
    #for reproducbility measures =============================================
    scores={}
    subp.check_output(['bash','-c','mkdir -p '+outdir+'/scores'])
    if methods_list==['all']:
        methods_list=['GenomeDISCO','HiCRep','HiC-Spector','QuASAR-Rep','QuASAR-QC']
    for method in methods_list:
        if method=="QuASAR-QC":
            continue
        scores[method]={}
        for line in open(metadata_pairs,'r').readlines():
            items=line.strip().split()
            samplename1,samplename2=items[0],items[1]
            scores[method][samplename1+'.vs.'+samplename2]={}
            #now, read in the scores
            for line in open(outdir+'/results/reproducibility/'+method+'/'+samplename1+'.vs.'+samplename2+'.txt','r'):
                items2=line.strip().split('\t')
                s1,s2,chromo,current_score=items2[0],items2[1],items2[2],float(items2[3])
                if subset_chromosomes!='NA':
                    if chromo not in subset_chromosomes.split(','):
                        continue
                scores[method][samplename1+'.vs.'+samplename2][chromo]=[current_score]
                if 'genomewide' not in scores[method][samplename1+'.vs.'+samplename2].keys():
                    scores[method][samplename1+'.vs.'+samplename2]['genomewide']=[]
                scores[method][samplename1+'.vs.'+samplename2]['genomewide'].append(current_score)
    
    #now, read quality scores
    scores_qc={}
    subp.check_output(['bash','-c','mkdir -p '+outdir+'/scores'])
    if methods_list==['all']:
        methods_list=['GenomeDISCO','HiCRep','HiC-Spector','QuASAR-Rep','QuASAR-QC']
    for method in methods_list:
        if method=="QuASAR-QC":
            scores_qc[method]={}
            for line in open(metadata_samples,'r').readlines():
                items=line.strip().split()
                samplename=items[0]
                scores_qc[method][samplename]={}
                #now, read in the scores            
                for filename in os.listdir(os.path.dirname(os.path.realpath(outdir+'/results/qc/'+samplename+'/QuASAR-QC/*'))):
                    if fnmatch.fnmatch(filename, '*.'+samplename+'.scores.txt'):
                        fname=os.path.dirname(os.path.realpath(outdir+'/results/qc'))+'/qc/'+samplename+'/QuASAR-QC/'+filename
                        for line2 in open(fname,'r').readlines():
                            items2=line2.strip().split('\t')
                            current_score=float(items2[1])
                            chromo=re.sub('.'+samplename+'.scores.txt','',os.path.basename(fname))
                            if subset_chromosomes!='NA':
                                if chromo not in subset_chromosomes.split(','):
                                    continue
                            scores_qc[method][samplename][chromo]=[current_score]
                            if 'genomewide' not in scores_qc[method][samplename].keys():
                                scores_qc[method][samplename]['genomewide']=[]
                            scores_qc[method][samplename]['genomewide'].append(current_score)

    chromo_lines=gzip.open(outdir+'/data/metadata/chromosomes.gz','r').readlines()
    chromo_lines.append('genomewide')
    methods_list_reproducibility=copy.deepcopy(methods_list)
    if 'all' in methods_list:
        methods_list_reproducibility=['GenomeDISCO','HiCRep','HiC-Spector','QuASAR-Rep']
    if 'QuASAR-QC' in methods_list_reproducibility:
        methods_list_reproducibility.remove('QuASAR-QC')
    if len(methods_list_reproducibility)>0:

        for chromo_line in chromo_lines:
            chromo=chromo_line.strip()
            if subset_chromosomes!='NA':
                if chromo not in subset_chromosomes.split(',') and chromo_line!='genomewide':
                    continue
            chromofile=open(outdir+'/scores/reproducibility.'+chromo+'.txt','w')
            methods_list_reproducibility.sort()
            chromofile.write('#Sample1\tSample2\t'+'\t'.join(methods_list_reproducibility)+'\n')
            for line in open(metadata_pairs,'r').readlines():
                items=line.strip().split()
                samplename1,samplename2=items[0],items[1]
                to_write=[samplename1,samplename2]
                for method_idx in range(len(methods_list_reproducibility)):
                    cur_score=str(0.001*int(1000*np.mean(np.array(scores[methods_list_reproducibility[method_idx]][samplename1+'.vs.'+samplename2][chromo]))))
                    to_write.append(cur_score)
                chromofile.write('\t'.join(to_write)+'\n')
            chromofile.close()

    #qc scores
    for method in methods_list:
        if method=="QuASAR-QC":
            for chromo_line in chromo_lines:
                chromo=chromo_line.strip()
                if subset_chromosomes!='NA':
                    if chromo not in subset_chromosomes.split(',') and chromo_line!='genomewide':
                        continue
                chromofile=open(outdir+'/scores/qc.'+chromo+'.txt','w')
                chromofile.write('#Sample\t'+'\t'+'QuASAR-QC'+'\n')
                for line in open(metadata_samples,'r').readlines():
                    items=line.strip().split()
                    samplename=items[0]
                    to_write=[samplename]
                    cur_score=str(0.001*int(1000*np.mean(np.array(scores_qc['QuASAR-QC'][samplename][chromo]))))
                    to_write.append(cur_score)
                    chromofile.write('\t'.join(to_write)+'\n')
                chromofile.close()

def visualize(outdir,parameters_file,metadata_pairs):
    header_col='FF0000'
    picsize="200"
    topscores=0.85    
    #TODO: add input from the calibration tables

    for line in open(metadata_pairs,'r').readlines():

        items=line.strip().split()
        samplename1,samplename2=items[0],items[1]

        #file_all_scores=open(outdir+'/results/GenomeDISCO/'+samplename1+'.vs.'+samplename2+'/genomewide_scores.'+samplename1+'.vs.'+samplename2+'.txt','w')
        print('GenomeDISCO | '+strftime("%c")+' | Writing report for '+samplename1+'.vs.'+samplename2)
        
        html_name=outdir+'/results/summary/report/'+samplename1+'.vs.'+samplename2+'.report.html'
        if not os.path.exists(os.path.dirname(html_name)):
            os.makedirs(os.path.dirname(html_name))
        html=open(outdir+'/results/summary/report/'+samplename1+'.vs.'+samplename2+'.report.html','w')
    
        html.write("<html>"+'\n')
        html.write("<head>"+'\n')
        html.write("<font color=\""+header_col+"\"> <strong>GenomeDISCO | Genomewide report </font></strong>"+'\n')
        html.write("<br>"+'\n')
        html.write("Report generated on "+strftime("%c")+'\n')
        html.write("<br>"+'\n')
        html.write("Code: <a href=\"http://github.com/kundajelab/genomedisco\">http://github.com/kundajelab/genomedisco</a>."+'\n')
        html.write("<br>"+'\n')
        html.write("Contact: Oana Ursu oursu@stanford.edu"+'\n')
        html.write("<br>"+'\n')
        html.write("<strong>"+samplename1+" vs "+samplename2+"</strong>"+'\n')
        html.write("</head>"+'\n')
        html.write("<body>"+'\n')
        html.write("<br>"+'\n')
        html.write("<br>"+'\n')
        
        #genomewide score
        html.write("<font color=\""+header_col+"\"> <strong>Reproducibility analysis</font></strong>"+'\n')
        html.write("<br>"+'\n')
        score_sum=0.0
        score_num=0
        scores=[]
        chromos=[]
        scoredict={}
        for chromo_line in gzip.open(outdir+'/data/metadata/chromosomes.gz','r').readlines():
            chromo=chromo_line.strip()
            f=outdir+'/results/reproducibility/'+samplename1+".vs."+samplename2+'/GenomeDISCO/'+chromo+'.'+samplename1+".vs."+samplename2+'.scores.txt'
            if os.path.isfile(f):
                score_num+=1
                score=float(open(f,'r').readlines()[0].split('\t')[2])
                score=float(int(1000*score))/1000.0
                score_sum+=score
                scores.append(score)
                chromos.append(chromo)
                scoredict[chromo]=score
        
        plt.close("all")
        widthfactor=3
        rcParams['figure.figsize'] = 10*widthfactor,10
        rcParams['xtick.labelsize'] = 20
        rcParams['ytick.labelsize'] = 20
        plt.scatter(range(len(chromos)),np.array(scores),s=100)
        plt.xticks(range(len(chromos)),chromos,rotation='vertical')
        plt.xlabel('chromosome',fontsize=30)
        plt.ylim(0.4,1.0)
        plt.axhline(topscores, color='r', linestyle='dashed',linewidth=2,label='threshold for high-quality datasets')
        plt.axhline(np.array(scores).mean(), color='b', linewidth=2,label='genomewide reproducibility for these datasets')
        plt.yticks([0.4,0.5,0.6,0.7,0.8,0.9,1.0])
        plt.ylabel('reproducibility',fontsize=30)
        plt.gcf().subplots_adjust(bottom=0.25)
        plt.gcf().subplots_adjust(left=0.25)
        plt.legend(loc=3,fontsize=25)
        plt.show()
        chrscores=outdir+'/results/reproducibility/'+samplename1+".vs."+samplename2+'/GenomeDISCO/'+samplename1+'.vs.'+samplename2+'.chrScores.png'
        plt.savefig(chrscores)
        plt.close()

        genomewide_score=score_sum/score_num
        
        html.write("<td> <strong>What is GenomeDISCO reproducibility?</strong></td>"+'\n')
        html.write("<br>"+'\n')
        html.write("GenomeDISCO (DIfferences between Smoothed COntact maps) computes reproducibility by comparing 2 contact maps at increasing levels of smoothing. The smoothing is done using random walks on graphs. For each dataset, we run random walks of increasing length, and ask what is the probability that we reach node j starting at node i, given a random walk through the network of t steps, or iterations. The key idea is that <strong>if 2 nodes are in contact, then there should be many high-confidence paths connecting them through the network</strong>, even if perhaps the direct edge between them was undersampled. Short random walks provide information about the local network structures, such as loop cliques and subdomains, whereas longer random walks shift the focus toward global structures such as compartments. For each random walk iteration we compare the 2 smoothed contact maps, obtaining an L1 difference in smoothed contact maps."+'\n')
        html.write("<br>"+'\n')
        html.write("In the end, we integrate information across all random walks by computing the area under the curve of L1 differences vs random walk iterations (see difference plot below), resulting in a dissimilarity score between the 2 contact maps of interest. We transform this dissimilarity into a reproducibility score using the formula \"Reproducibility = 1-d\". This yields a reproducibility score between -1 and 1, with higher values indicating similarity (in practice, the range of scores is [0.4,1])."+'\n')
        html.write("<br>"+'\n')
        html.write("GenomeDISCO runs on each chromosome separately. The genomewide score reported below is the average across all chromosomes. <strong> Higher scores are better</strong>.")
        html.write("<br>"+'\n')
        html.write("<br>"+'\n')
        html.write("<font color=\""+header_col+"\"><strong> Your scores</strong></font>"+'\n')
        html.write("<br>"+'\n')
        html.write("<img src=\""+"../../reproducibility/"+samplename1+".vs."+samplename2+'/GenomeDISCO/'+os.path.basename(chrscores)+"\" width=\""+str(int(1.3*int(picsize))*widthfactor)+"\" height=\""+str(1.3*int(picsize))+"\">"+'\n')
        html.write("<br>"+'\n')
        html.write("<br>"+'\n')
        html.write("Reproducibility (genomewide) = "+str(float("{0:.3f}".format(float(genomewide_score))))+'\n')
        
        if genomewide_score>=topscores:
            outcome='Congratulations! These datasets are highly reproducible.'
        else:
            outcome='These datasets are less reproducible than our empirically defined threshold. This could be due to low sequencing depth, differences in distance dependence curves, noise. Please be cautious with these datasets.'
        html.write("<br>"+'\n')
        html.write("<br>"+'\n')
        html.write("<font color=\"0033FF\"><strong>"+outcome+"</strong></font>"+'\n')
        html.write("<br>"+'\n')
        html.write("<br>"+'\n')
        html.write("<font color=\""+header_col+"\"> <strong>Analysis by chromosome</font></strong>"+'\n')
        html.write("<br>"+'\n')
        '''
        html.write("<td> <strong>The difference plot</strong></td>"+'\n')
        html.write(" shows the L1 difference (normalized to the number of nodes) as a function of random walk iteration."+'\n')
        html.write("<br>"+'\n')
        '''
        html.write("<td> <strong>The distance dependence plot</strong></td>"+'\n')
        html.write(" shows the probability of contact as a function of linear genomic distance. If 2 datasets have very difference distance dependence curves, their reproducibility will be lower than if they have similar curves."+'\n')
        html.write("<br>"+'\n')
        html.write("<td> <strong>The remaining columns</strong></td>"+'\n')
        html.write(" below show the contact maps after smoothing with random walks. The upper triangular part plotted in red is "+samplename1+", while the blue is "+samplename2+". The colorbar shows red values as positive and blue values as negative purely for visualization purposes (in reality all values are positive)."+'\n')
        html.write("<br>"+'\n')
        html.write("<br>"+'\n')
    
        #big table
        html.write("<table border=\"1\" cellpadding=\"10\" cellspacing=\"0\" style=\"border-collapse:collapse;\">"+'\n')
        html.write("<tr>"+'\n')
        html.write("<td> </td>"+'\n')
        html.write("<td> <strong><center>seq. depth, subs. seq. depth</center></strong></td>"+'\n')
        html.write("<td> <strong><center>GenomeDISCO score</center></strong></td>"+'\n')
        #html.write("<td> <strong><center>difference plot</center></strong></td>"+'\n')
        html.write("<td> <strong><center>distance dependence</center></td>"+'\n')
        
        #======
        tmin=3
        tmax=3

        for t in range(tmin,tmax+1):
            html.write("<td><center><strong>Random walk iteration "+str(t)+"</strong></center></td>"+'\n')
        html.write("</tr>"+'\n')

        
        score_strings=[]
        chromo_strings=[]
        sorted_chromos=gzip.open(outdir+'/data/metadata/chromosomes.gz','r').readlines()
        sorted_chromos.sort()
        for chromo_idx in range(len(sorted_chromos)):
            chromo=sorted_chromos[chromo_idx].strip()
            f1=outdir+'/data/edges/'+samplename1+'/'+samplename2+'.'+chromo+'.gz'
            f2=outdir+'/data/edges/'+samplename1+'/'+samplename2+'.'+chromo+'.gz'
            f=outdir+'/results/reproducibility/'+samplename1+".vs."+samplename2+'/GenomeDISCO/'+chromo+'.'+samplename1+".vs."+samplename2+'.scores.txt'
            sf=outdir+'/results/reproducibility/'+samplename1+".vs."+samplename2+'/GenomeDISCO/'+chromo+'.'+samplename1+".vs."+samplename2+'.datastats.txt'
            
            if os.path.isfile(f):
                chromo_strings.append(chromo)
                items=open(sf,'r').readlines()[1].strip().split('\t')
                s1,s2,ssub1,ssub2=items[2:6]
                s1=str(float("{0:.2f}".format(float(float(s1)/1000000))))
                s2=str(float("{0:.2f}".format(float(float(s2)/1000000))))
                ssub1=str(float("{0:.2f}".format(float(float(ssub1)/1000000))))
                ssub2=str(float("{0:.2f}".format(float(float(ssub2)/1000000))))
                html.write("<tr>"+'\n')
                html.write("<td> <strong> "+chromo+"</strong></td>"+'\n')
                score=scoredict[chromo]
                html.write("<td> "+samplename1+": "+str(s1)+', '+str(ssub1)+' M'+'\n')
                html.write("<br>"+'\n')
                html.write("<br>"+'\n')
                html.write(samplename2+": "+str(s2)+', '+str(ssub2)+" M </td>"+'\n')
                score_strings.append(str(float("{0:.3f}".format(float(score)))))
                html.write("<td> "+str(float("{0:.3f}".format(float(score))))+" </td>"+'\n')
                '''
                diffplot="../../reproducibility/"+samplename1+".vs."+samplename2+'/GenomeDISCO/'+chromo+"."+samplename1+".vs."+samplename2+".DiscoRandomWalks.Differences.png"
                
                html.write("<td> <img src=\""+diffplot+"\" width=\""+picsize+"\" height=\""+picsize+"\"> </td>"+'\n')
                '''
                dd="../../reproducibility/"+samplename1+".vs."+samplename2+'/GenomeDISCO/'+chromo+"."+samplename1+".vs."+samplename2+".distDep.png"
                html.write("<td> <img src=\""+dd+"\" width=\""+picsize+"\" height=\""+picsize+"\"> </td>"+'\n')
                for t in range(tmin,tmax+1):
                    pic="../../reproducibility/"+samplename1+".vs."+samplename2+'/GenomeDISCO/'+chromo+"."+samplename1+".vs."+samplename2+".DiscoRandomWalks."+str(t)+".png"
                    html.write("<td> <img src=\""+pic+"\" width=\""+picsize+"\" height=\""+picsize+"\"></td>"+'\n')
                html.write("</tr>"+'\n')
        
        html.write("</table>"+'\n')
        html.write("<br>"+'\n')
        html.write("</body>"+'\n')
        html.write("</html>"+'\n')

def clean_up(outdir):
    subp.check_output(['bash','-c','rm -r '+outdir+'/results'])
    subp.check_output(['bash','-c','rm -r '+outdir+'/data'])
    subp.check_output(['bash','-c','rm -r '+outdir+'/scripts'])

def run_all(metadata_samples,metadata_pairs,bins,re_fragments,methods,parameters_file,outdir,running_mode,concise_analysis,subset_chromosomes,timing):
    preprocess(metadata_samples,bins,re_fragments,methods,outdir,running_mode,subset_chromosomes,parameters_file,timing)
    get_qc(metadata_samples,methods,outdir,running_mode,concise_analysis,subset_chromosomes,timing)
    concordance(metadata_pairs,methods,outdir,running_mode,concise_analysis,subset_chromosomes,timing)
    summary(metadata_samples,metadata_pairs,bins,re_fragments,methods,outdir,running_mode,concise_analysis,subset_chromosomes)
    clean_up(outdir)
