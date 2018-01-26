step=$1
substep=$2

#=======================================
DATA=/ifs/scratch/oursu/paper_2017-12-20
resolutions=10000,50000,500000
MYCODE=/srv/gsfs0/projects/kundaje/users/oursu/code
MAPQ=30
mypython=/srv/gsfs0/projects/kundaje/users/oursu/code/anaconda2/mypython/bin/python
chrSizes=${DATA}/data/chrSizes.hg19.txt
macs2=/srv/gsfs0/projects/kundaje/users/oursu/code/anaconda2/mypython/bin/macs2
#=======================================


if [[ ${step} == "setup_folder" ]];
then
    mkdir -p ${DATA}
    mkdir -p ${DATA}/data
    cp /srv/gsfs0/projects/kundaje/commonRepository/annotations/human/hg19.GRCh37/genomeSize/hg19.genome ${chrSizes}
    cp /srv/gsfs0/projects/snyder/oursu/software/git/public_genomedisco/genomedisco/paper_analysis/2017-06-08/real/LA_metadata.txt ${DATA}/data/
fi

if [[ ${step} == "install_code" ]];
then
    #3DChromatin_ReplicateQC
    cd ${MYCODE}
    git clone http://github.com/kundajelab/3DChromatin_ReplicateQC
    cd 3DChromatin_ReplicateQC
    install_scripts/install_3DChromatin_ReplicateQC.sh --pathtopython /srv/gsfs0/projects/kundaje/users/oursu/code/anaconda2/mypython/bin/python --pathtor R --rlib /srv/gsfs0/projects/kundaje/users/oursu/code/Rlibs --pathtobedtools bedtools --modules R/3.4.1,bedtools/2.26.0
    #for hic file extraction
    mkdir -p ${MYCODE}/juicer_tools
    cd ${MYCODE}/juicer_tools
    wget http://hicfiles.tc4ga.com.s3.amazonaws.com/public/juicer/juicer_tools.1.7.5_linux_x64_jcuda.0.8.jar
    #genome_utils
    git clone https://github.com/oursu/genome_utils
    #macs2
    /srv/gsfs0/projects/kundaje/users/oursu/code/anaconda2/mypython/bin/pip install MACS2
fi

if [[ ${step} == "get_Rao_data" ]];
then
    if [[ ${substep} == "hic_files" ]];
    then
	mkdir -p ${DATA}/Rao_data/hic
	mv /ifs/scratch/oursu/data/hic/* ${DATA}/Rao_data/hic/
	for f in $(ls ${DATA}/Rao_data/hic/*gz);
	do
	    gunzip $f
	done
    fi
    if [[ ${substep} == "individual_reads" ]];
    then
	mkdir -p ${DATA}/Rao_data/counts
	mv /srv/gsfs0/projects/kundaje/users/oursu/3d/LA/merged_nodups/data/* ${DATA}/Rao_data/counts/
    fi
fi

if [[ ${step} == "Rao" ]];
then
    if [[ ${substep} == "resolutions_hic_files" ]];
    then
	for f in $(ls ${DATA}/Rao_data/hic/*hic);
	do
	    s=${DATA}/Rao_data/hic/split_$(basename ${f}).sh
	    echo "module load java/latest" > ${s}
	    for res in $(echo ${resolutions} | sed 's/,/ /g');
	    do
		mkdir -p ${DATA}/Rao_data/hic/res${res}
		for chromo in $(echo "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,X" | sed 's/,/ /g');
		do
		    out=${DATA}/Rao_data/hic/res${res}/$(basename ${f}).res${res}.chr${chromo}.gz
		    echo "/usr/java/latest/bin/java -jar ${MYCODE}/juicer_tools/juicer_tools.1.7.5_linux_x64_jcuda.0.8.jar dump observed NONE ${f} ${chromo} ${chromo} BP ${res} ${out}.f" >> ${s}
		    echo "zcat -f ${out}.f | awk -v chromosome=${chromo} '{print chromosome\"\t\""'$'"1\"\t\"chromosome\"\t\""'$'"2\"\t\""'$'"3}' | gzip > ${out}" >> ${s}
		    echo "rm ${out}.f" >> ${s}
		done
	    done
            chmod 755 ${s}
	    $s
	done
	#do the gm separately
	for chromo in $(echo "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,X" | sed 's/,/ /g');
	do
	    echo ${chromo}
	    zcat -f ${DATA}/Rao_data/hic/GM12878_combined/10kb_resolution_intrachromosomal/chr${chromo}/MAPQGE30/chr${chromo}_10kb.RAWobserved | awk -v chromosome=${chromo} '{print chromosome"\t"$1"\t"chromosome"\t"$2"\t"$3}' | gzip > ${DATA}/Rao_data/hic/res10000/GM12878_combined.res10000.chr${chromo}.gz
	done
	for chromo in $(echo "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,X" | sed 's/,/ /g');
        do
            echo ${chromo}
            zcat -f ${DATA}/Rao_data/hic/GM12878_combined/50kb_resolution_intrachromosomal/chr${chromo}/MAPQGE30/chr${chromo}_50kb.RAWobserved | awk -v chromosome=${chromo} '{print chromosome"\t"$1"\t"chromosome"\t"$2"\t"$3}' | gzip > ${DATA}/Rao_data/hic/res50000/GM12878_combined.res50000.chr${chromo}.gz
        done
	for chromo in $(echo "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,X" | sed 's/,/ /g');
        do
            echo ${chromo}
            zcat -f ${DATA}/Rao_data/hic/GM12878_combined/500kb_resolution_intrachromosomal/chr${chromo}/MAPQGE30/chr${chromo}_500kb.RAWobserved | awk -v chromosome=${chromo} '{print chromosome"\t"$1"\t"chromosome"\t"$2"\t"$3}' | gzip > ${DATA}/Rao_data/hic/res500000/GM12878_combined.res500000.chr${chromo}.gz
        done

	for cellline in GM12878_combined HMEC HUVEC IMR90 K562 KBM7 NHEK;
	do
	    echo ${cellline}
	    for res in $(echo ${resolutions} | sed 's/,/ /g');
	    do
		zcat -f ${DATA}/Rao_data/hic/res${res}/*${cellline}*chr*gz | gzip > ${DATA}/Rao_data/hic/res${res}/${cellline}.res${res}.gz
	    done
	done
    fi

    if [[ ${substep} == "resolutions_reads_files" ]];
    then
	for f in $(ls ${DATA}/Rao_data/counts/*gz);
	do
	    for res in $(echo ${resolutions} | sed 's/,/ /g');
            do 
		mkdir -p ${DATA}/Rao_data/counts/res${res}
		#once for the whole genome
		out=${DATA}/Rao_data/counts/res${res}/$(basename ${f} | sed 's/_merged_nodups[.]txt[.]gz[.]//g' | sed 's/_/\t/g' | cut -f2).res${res}.gz
		s=${out}.sh
		echo ${out}
		echo "${MYCODE}/genome_utils/3Dutils/LA_reads_to_n1n2value_bins.sh ${f} ${out} ${MAPQ} intra ${res}" > ${s}
		echo "rm ${s}" >> ${s}
		chmod 755 ${s}
		qsub -o ${s}.o -e ${s}.e ${s}
	    done
	done
    fi
fi

if [[ ${step} == "Rao_metadata" ]];
then
    for res in $(echo ${resolutions} | sed 's/,/ /g');
    do
	#metadata samples
	mkdir -p ${DATA}/results/metadata
	metadata_samples=${DATA}/results/metadata/metadata.samples.res${res}
	rm ${metadata_samples}
	for dataset_number in {1..83};
        do
            dataset="HIC"$(echo "00${dataset_number}" | sed 's/.*\(...\)/\1/')
	    echo "${dataset}delim${DATA}/Rao_data/counts/res${res}/${dataset}.res${res}.gz" | sed 's/delim/\t/g' >> ${metadata_samples}
	done

	#metadata pairs
	metadata_pairs=${DATA}/results/metadata/metadata.pairs.res${res}
	rm ${metadata_pairs}*
	#odds
	for data1 in $(zcat -f ${metadata_samples} | cut -f1 | sed -n 'p;n');
	do
	    for data2 in $(zcat -f ${metadata_samples} | cut -f1 | sed -n 'p;n');
	    do
		echo "${data1}delim${data2}" | sed 's/delim/\t/g' >> ${metadata_pairs}.tmp
	    done
	done
	#evens
	for data1 in $(zcat -f ${metadata_samples} | cut -f1 | sed -n 'n;p');
        do
            for data2 in $(zcat -f ${metadata_samples} | cut -f1 | sed -n 'n;p');
            do
                echo "${data1}delim${data2}" | sed 's/delim/\t/g' >> ${metadata_pairs}.tmp
            done
        done

	${mypython} ${MYCODE}/3DChromatin_ReplicateQC/software/genomedisco/genomedisco/scripts/orderpairs.py --file ${metadata_pairs}.tmp --out ${metadata_pairs}.tmp2
	cat ${metadata_pairs}.tmp2 | sort | uniq | awk '{if ($1!=$2) print $0}' > ${metadata_pairs}
	rm ${metadata_pairs}.tmp*
	echo ${metadata_pairs}
    done
fi

if [[ ${step} == "bins" ]];
then
    source ${MYCODE}/3DChromatin_ReplicateQC/configuration_files/bashrc.configuration
    for res in $(echo ${resolutions} | sed 's/,/ /g');
    do
	mkdir -p ${DATA}/results/bins
	bedtools makewindows -w ${res} -g ${chrSizes} | awk '{print $1"\t"$2"\t"$3"\t"$2}' | gzip > ${DATA}/results/bins/bins.res${res}.gz
    done
fi

if [[ ${step} == "Rao_runs" ]];
then
    for res in 50000; #$(echo ${resolutions} | sed 's/,/ /g');
    do
	out=${DATA}/results/rao/res${res}
	bins=${DATA}/results/bins/bins.res${res}.gz
        metadata_samples=${DATA}/results/metadata/metadata.samples.res${res}
	metadata_pairs=${DATA}/results/metadata/metadata.pairs.res${res}

	if [[ ${substep} == "split" ]];
	then
	    ${mypython} ${MYCODE}/3DChromatin_ReplicateQC/3DChromatin_ReplicateQC.py split --metadata_samples ${metadata_samples} --bins ${bins} --outdir ${out} --methods GenomeDISCO,HiCRep,HiC-Spector --running_mode sge
	fi

	if [[ ${substep} == "split_transition" ]];
        then
	    out=${DATA}/results/rao/res${res}.keepDiag.transition
            ${mypython} ${MYCODE}/3DChromatin_ReplicateQC/3DChromatin_ReplicateQC.py split --metadata_samples ${metadata_samples} --bins ${bins} --outdir ${out} --methods GenomeDISCO,HiCRep,HiC-Spector --running_mode sge
        fi

	if [[ ${substep} == "run" ]];
        then
	    echo "here"
	    echo ${metadata_pairs}
            ${mypython} ${MYCODE}/3DChromatin_ReplicateQC/3DChromatin_ReplicateQC.py reproducibility --metadata_pairs ${metadata_pairs} --outdir ${out} --methods GenomeDISCO --parameters_file ${MYCODE}/3DChromatin_ReplicateQC/examples/example_parameters.bystep.txt --subset_chromosomes chr2 --concise_analysis --running_mode sge #--parameters_file ${MYCODE}/3DChromatin_ReplicateQC/examples/example_parameters.bystep.10steps.transition.txt
	fi

	if [[ ${substep} == "run_transition" ]];
        then
	    out=${DATA}/results/rao/res${res}.keepDiag.transition
            echo ${metadata_pairs}
            ${mypython} ${MYCODE}/3DChromatin_ReplicateQC/3DChromatin_ReplicateQC.py reproducibility --metadata_pairs ${metadata_pairs} --outdir ${out} --methods GenomeDISCO --subset_chromosomes chr21 --concise_analysis --running_mode sge --parameters_file ${MYCODE}/3DChromatin_ReplicateQC/examples/example_parameters.bystep.10steps.transition.txt                                                   
        fi

	if [[ ${substep} == "compile_scores" ]];
        then
	    echo "here"
	    mkdir -p ${DATA}/results/rao/res${res}/compiled_scores
	    echo ${DATA}/results/rao/res${res}/compiled_scores
	    for chromo in 21;
	    do
		zcat -f ${DATA}/results/rao/res${res}/results/reproducibility/GenomeDISCO/chr${chromo}.*.scoresByStep.txt | grep -v m1 > ${DATA}/results/rao/res${res}/compiled_scores/chr${chromo}.GenomeDISCO.scores.txt
		zcat -f ${DATA}/results/rao/res${res}/results/reproducibility/HiCRep/chr${chromo}.*.scores.txt > ${DATA}/results/rao/res${res}/compiled_scores/chr${chromo}.HiCRep.scores.txt
		zcat -f ${DATA}/results/rao/res${res}/results/reproducibility/HiC-Spector/chr${chromo}.*.scores.txt > ${DATA}/results/rao/res${res}/compiled_scores/chr${chromo}.HiC-Spector.scores.txt
	    done
	fi

	if [[ ${substep} == "compile_scores_transition" ]];
        then
            echo "here"
	    d=${DATA}/results/rao/res${res}.keepDiag.transition
            mkdir -p ${d}/compiled_scores
            for chromo in 21;
            do
                zcat -f ${d}/results/reproducibility/GenomeDISCO/chr${chromo}.*.scoresByStep.txt | grep -v m1 > ${d}/compiled_scores/chr${chromo}.GenomeDISCO.scores.txt
                zcat -f ${d}/results/reproducibility/HiCRep/chr${chromo}.*.scores.txt > ${d}/compiled_scores/chr${chromo}.HiCRep.scores.txt
                zcat -f ${d}/results/reproducibility/HiC-Spector/chr${chromo}.*.scores.txt > ${d}/compiled_scores/chr${chromo}.HiC-Spector.scores.txt
            done
        fi

    done
fi

if [[ ${step} == "HiChIP" ]]; 
then
    mkdir -p ${DATA}/HiChIP_data
    mkdir -p ${DATA}/results/HiChIP
    if [[ ${substep} == "download" ]];
    then
	cd ${DATA}/HiChIP_data
	wget ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2705nnn/GSM2705041/suppl/GSM2705041_GM_HiChIP_H3K27ac_B1_allValidPairs.txt.gz
	wget ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2705nnn/GSM2705042/suppl/GSM2705042_GM_HiChIP_H3K27ac_B2_allValidPairs.txt.gz
	wget ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2705nnn/GSM2705043/suppl/GSM2705043_K562_HiChIP_H3K27ac_B1_allValidPairs.txt.gz
	wget ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2705nnn/GSM2705044/suppl/GSM2705044_K562_HiChIP_H3K27ac_B2_allValidPairs.txt.gz
	wget ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2705nnn/GSM2705045/suppl/GSM2705045_K562_HiChIP_H3K27ac_B3_allValidPairs.txt.gz
	wget ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2705nnn/GSM2705046/suppl/GSM2705046_MyLa_HiChIP_H3K27ac_B1_allValidPairs.txt.gz
	wget ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2705nnn/GSM2705047/suppl/GSM2705047_MyLa_HiChIP_H3K27ac_B2_allValidPairs.txt.gz
	wget ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2705nnn/GSM2705048/suppl/GSM2705048_Naive_HiChIP_H3K27ac_B1T1_allValidPairs.txt.gz
	wget ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2705nnn/GSM2705049/suppl/GSM2705049_Naive_HiChIP_H3K27ac_B2T1_allValidPairs.txt.gz
	wget ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2705nnn/GSM2705050/suppl/GSM2705050_Naive_HiChIP_H3K27ac_B2T2_allValidPairs.txt.gz
	wget ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2705nnn/GSM2705051/suppl/GSM2705051_Naive_HiChIP_H3K27ac_B3T1_allValidPairs.txt.gz
	wget ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2705nnn/GSM2705052/suppl/GSM2705052_Naive_HiChIP_H3K27ac_B3T2_allValidPairs.txt.gz
	wget ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2705nnn/GSM2705053/suppl/GSM2705053_Th17_HiChIP_H3K27ac_B1T1_allValidPairs.txt.gz
	wget ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2705nnn/GSM2705054/suppl/GSM2705054_Th17_HiChIP_H3K27ac_B1T2_allValidPairs.txt.gz
	wget ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2705nnn/GSM2705055/suppl/GSM2705055_Th17_HiChIP_H3K27ac_B2T1_allValidPairs.txt.gz
	wget ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2705nnn/GSM2705056/suppl/GSM2705056_Th17_HiChIP_H3K27ac_B3T1_allValidPairs.txt.gz
	wget ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2705nnn/GSM2705057/suppl/GSM2705057_Treg_HiChIP_H3K27ac_B1T1_allValidPairs.txt.gz
	wget ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2705nnn/GSM2705058/suppl/GSM2705058_Treg_HiChIP_H3K27ac_B2T1_allValidPairs.txt.gz
	wget ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2705nnn/GSM2705059/suppl/GSM2705059_Treg_HiChIP_H3K27ac_B3T1_allValidPairs.txt.gz
	wget ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2705nnn/GSM2705060/suppl/GSM2705060_Naive_HiChIP_CTCF_B1_allValidPairs.txt.gz
	wget ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2705nnn/GSM2705061/suppl/GSM2705061_Naive_HiChIP_CTCF_B2_allValidPairs.txt.gz
	wget ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2705nnn/GSM2705062/suppl/GSM2705062_HCASMC_HiChIP_H3K27ac_B1T1_allValidPairs.txt.gz
	wget ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2705nnn/GSM2705063/suppl/GSM2705063_HCASMC_HiChIP_H3K27ac_B1T2_allValidPairs.txt.gz
	wget ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2705nnn/GSM2705064/suppl/GSM2705064_HCASMC_HiChIP_H3K27ac_B1T3_allValidPairs.txt.gz
    fi

    if [[ ${substep} == "process_valid_pairs" ]];
    then
	mkdir -p ${DATA}/HiChIP_data/merged_techreps
	for cellline in K562 HCASMC Treg Th17 GM MyLa Naive;
	do
	    for chipped in H3K27ac;
	    do
	        for rep in 1 2 3;
		do
		    dir_of_files=${DATA}/HiChIP_data
		    if [[ $(ls ${dir_of_files}/GSM*_${cellline}_HiChIP_${chipped}_B${rep}*_allValidPairs.txt.gz | wc -l) > 0 ]];
		    then
			outname=${DATA}/HiChIP_data/merged_techreps/HiChIP.${cellline}_${chipped}.Rep${rep}.reads.gz
			s=${outname}.sh
			echo '#!/bin/sh' > ${s}
			echo "zcat -f ${dir_of_files}/GSM*_${cellline}_HiChIP_${chipped}_B${rep}*_allValidPairs.txt.gz | awk '{if ("'$'"2=="'$'"5) print "'$'"0}' | awk '{print \"NA\tNA\t\""'$'"2\"\t\""'$'"3\"\tNA\tNA\t\""'$'"5\"\t\""'$'"6\"\tNA\t31\t31\"}' | gzip > ${outname}" >> ${s}
			chmod 755 ${s}
			qsub -o ${s}.o -e ${s}.e ${s}
		    fi
		done
	    done
	done
    fi

    if [[ ${substep} == "fixed_bin_reads" ]];
    then
	BINNED=${DATA}/HiChIP_data/merged_techreps/binned
	for cellline in K562 HCASMC Treg Th17 GM MyLa Naive;
	do
            for chipped in H3K27ac;
            do
	        for res in $(echo ${resolutions} | sed 's/,/ /g');
		do
		    for method in HiChIP; #ChIA-PET;
		    do
			samples=$(ls ${DATA}/HiChIP_data/merged_techreps/${method}.${cellline}_${chipped}.Rep*.reads.gz)
			echo ${samples}
			for samplefile in ${samples};
			do
			    mkdir -p ${BINNED}_res${res}
			    outname=${BINNED}_res${res}/$(basename ${samplefile}).res${res}.gz
			    s=${outname}.sh
			    echo '#!/bin/sh' > ${s}
			    echo "${MYCODE}/genome_utils/3Dutils/LA_reads_to_n1n2value_bins.sh ${samplefile} ${outname} 30 intra ${res}" >> ${s}
			    chmod 755 ${s}
			    qsub -o ${s}.o -e ${s}.e ${s}
			done
		    done
		done
	    done
	done
    fi

    metadata_samples=${DATA}/HiChIP_data/metadata/metadata.diffcell.samples
    metadata_pairs=${DATA}/HiChIP_data/metadata/metadata.diffcell.pairs

    if [[ ${substep} == "metadata_diffcell" ]];
    then
	mkdir -p ${DATA}/HiChIP_data/metadata
	rm ${metadata_samples}*
	rm ${metadata_pairs}*

        #samples                                                                                                                                    
	for cellline in K562 HCASMC Treg Th17 GM MyLa Naive;
	do
            for chipped in H3K27ac;
            do
		for method in HiChIP; #ChIA-PET;                                                                                                    
		do
                    samples=$(ls ${DATA}/HiChIP_data/merged_techreps/${method}.${cellline}_${chipped}.Rep*.reads.gz)
                    for samplefile in ${samples};
                    do
			for res in $(echo ${resolutions} | sed 's/,/ /g');
			do
                            outname=${DATA}/HiChIP_data/merged_techreps/binned_res${res}/$(basename ${samplefile}).res${res}.gz
                            echo "$(basename ${samplefile})_res${res}__${outname}" | sed 's/__/\t/g' >> ${metadata_samples}.res${res}
			done
                    done
		done
            done
	done
	#pairs
	method=HiChIP
	for cell1 in K562 HCASMC Treg Th17 GM MyLa Naive;
	do
	    samples1=$(ls ${DATA}/HiChIP_data/merged_techreps/${method}.${cell1}_${chipped}.Rep*.reads.gz)
            for samplefile1 in ${samples1};
            do
	        for cell2 in K562 HCASMC Treg Th17 GM MyLa Naive;
		do
		    samples2=$(ls ${DATA}/HiChIP_data/merged_techreps/${method}.${cell2}_${chipped}.Rep*.reads.gz)
		    for samplefile2 in ${samples2};
		    do
			for chipped in H3K27ac;
			do
			    echo "$(basename ${samplefile1})__$(basename ${samplefile2})" | sed 's/__/\t/g' >> ${metadata_pairs}
			    for res in $(echo ${resolutions} | sed 's/,/ /g');
			    do
				echo "$(basename ${samplefile1})_res${res}__$(basename ${samplefile2})_res${res}" | sed 's/__/\t/g' >> ${metadata_pairs}.res${res}
			    done
			done
		    done
		done
	    done
	done
	echo ${metadata_pairs}.res${res}
    fi

    for res in 50000; #$(echo ${resolutions} | sed 's/,/ /g');
    do
	out=${DATA}/results/HiChIP/res${res}
	bins=${DATA}/results/bins/bins.res${res}.gz
    
	if [[ ${substep} == "split" ]];
	then
            ${mypython} ${MYCODE}/3DChromatin_ReplicateQC/3DChromatin_ReplicateQC.py split --metadata_samples ${metadata_samples}.res${res} --bins ${bins} --outdir ${out} --methods GenomeDISCO,HiCRep,HiC-Spector --running_mode sge 
	fi

	if [[ ${substep} == "split_keepDiag" ]];
        then
	    out=${DATA}/results/HiChIP/res${res}_keepDiag
            ${mypython} ${MYCODE}/3DChromatin_ReplicateQC/3DChromatin_ReplicateQC.py split --metadata_samples ${metadata_samples}.res${res} --bins ${bins} --outdir ${out} --methods GenomeDISCO,HiCRep,HiC-Spector --running_mode sge
        fi

	if [[ ${substep} == "split_transition" ]];
        then
            out=${DATA}/results/HiChIP/res${res}_transition
            ${mypython} ${MYCODE}/3DChromatin_ReplicateQC/3DChromatin_ReplicateQC.py split --metadata_samples ${metadata_samples}.res${res} --bins ${bins} --outdir ${out} --methods GenomeDISCO,HiCRep,HiC-Spector --running_mode sge
        fi
	
	if [[ ${substep} == "run" ]];
	then
            ${mypython} ${MYCODE}/3DChromatin_ReplicateQC/3DChromatin_ReplicateQC.py reproducibility --metadata_pairs ${metadata_pairs}.res${res} --outdir ${out} --methods GenomeDISCO --parameters_file ${MYCODE}/3DChromatin_ReplicateQC/examples/example_parameters.bystep.10steps.txt --subset_chromosomes chr21 --concise_analysis --running_mode sge 
	fi

	if [[ ${substep} == "run_keepDiag" ]];
        then
	    out=${DATA}/results/HiChIP/res${res}_keepDiag
            ${mypython} ${MYCODE}/3DChromatin_ReplicateQC/3DChromatin_ReplicateQC.py reproducibility --metadata_pairs ${metadata_pairs}.res${res} --outdir ${out} --methods GenomeDISCO --parameters_file ${MYCODE}/3DChromatin_ReplicateQC/examples/example_parameters.bystep.10steps.keepDiag.txt --subset_chromosomes chr21 --concise_analysis --running_mode sge
        fi

	if [[ ${substep} == "run_transition" ]];
        then
            out=${DATA}/results/HiChIP/res${res}_transition
            ${mypython} ${MYCODE}/3DChromatin_ReplicateQC/3DChromatin_ReplicateQC.py reproducibility --metadata_pairs ${metadata_pairs}.res${res} --outdir ${out} --methods HiCRep,HiC-Spector --parameters_file ${MYCODE}/3DChromatin_ReplicateQC/examples/example_parameters.bystep.10steps.transition.txt --subset_chromosomes chr21 --concise_analysis --running_mode sge
        fi
	 
	if [[ ${substep} == "count_reads" ]];
	then
	    rm ${metadata_samples}.res${res}.counts
	    while read line
	    do
		read -a items <<< "$line"
		samplename=${items[0]}
		samplefile=${items[1]}
		echo ${samplename}
		zcat -f ${samplefile} | awk -v sname=${samplename} '{sum+=$5} END {print sname"\t"sum}' >> ${metadata_samples}.res${res}.counts
	    done < ${metadata_samples}.res${res}
	fi
    done

    if [[ ${substep} == "compare_k562peaks" ]];
    then
	module load bedtools/2.26.0
	#scp oursu@nandi.stanford.edu:/mnt/data/epigenomeRoadmap/peaks/consolidated/narrowPeak/E123-H3K27ac.narrowPeak.gz ${DATA}/data/
	total_chip=$(zcat -f ${DATA}/data/E123-H3K27ac.narrowPeak.gz | wc -l)
	for w in 0 100 500 1000;
	do
	    echo "window: ${w}=============="
	    for q in 1 5 10 15 20;
	    do
		total_hichip=$(zcat -f ${DATA}/HiChIP_data/self_ligations/dist8000/HiChIP.K562_H3K27ac.Rep2.self_lig.gz_peaks/HiChIP.K562_H3K27ac.Rep2_peaks.narrowPeak | awk -v qval=${q} '{if ($9>=qval) print $0}' | wc -l)
		overlapping_chip=$(zcat -f ${DATA}/HiChIP_data/self_ligations/dist8000/HiChIP.K562_H3K27ac.Rep2.self_lig.gz_peaks/HiChIP.K562_H3K27ac.Rep2_peaks.narrowPeak | awk -v qval=${q} '{if ($9>=qval) print $0}' | bedtools window -w ${w} -u -a stdin -b ${DATA}/data/E123-H3K27ac.narrowPeak.gz | wc -l)
		overlapping_hichip=$(zcat -f ${DATA}/HiChIP_data/self_ligations/dist8000/HiChIP.K562_H3K27ac.Rep2.self_lig.gz_peaks/HiChIP.K562_H3K27ac.Rep2_peaks.narrowPeak | awk -v qval=${q} '{if ($9>=qval) print $0}' | bedtools window -w ${w} -u -a ${DATA}/data/E123-H3K27ac.narrowPeak.gz -b stdin | wc -l)
		echo "-log10qvalue ${q}: ${overlapping_chip}/${total_hichip} hichip peaks overlap ChIP-seq peaks, and ${overlapping_hichip}/${total_chip} ChIP-seq peaks covered"
	    done
	done
    fi

    if [[ ${substep} == "validPairs_2_macs2reads" ]];
    then
	while read line
        do
            read -a items <<< "$line"
            samplename=$(echo ${items[0]} | sed 's/_res50000//g')
	    dataname=$(echo ${samplename} | sed 's/[.]reads[.]gz//g')
            samplefile=${items[1]}
	    validPairs=${DATA}/HiChIP_data/merged_techreps/${samplename}
	    echo ${dataname}
            #make validPairs into reads for input to macs2
	    selfligation_dist=8000
	    mkdir -p ${DATA}/HiChIP_data/self_ligations/dist${selfligation_dist}
	    self_lig=${DATA}/HiChIP_data/self_ligations/dist${selfligation_dist}/${dataname}.self_lig.gz
	    s=${self_lig}.sh
	    echo '#!/bin/sh' > ${s}
	    echo "zcat -f ${validPairs} | awk -v selflig_dist=${selfligation_dist} '{dist="'$'"4-"'$'"8}{if (dist<0) dist=-dist}{if ((dist<=selflig_dist) && ("'$'"3=="'$'"7)) print "'$'"3\"\t\"("'$'"4-37)\"\t\"("'$'"4+38)\"\n\""'$'"7\"\t\"("'$'"8-37)\"\t\"("'$'"8+38)}' | gzip > ${self_lig}" >> ${s}
	    gsize=2700000000
	    mkdir -p ${self_lig}_peaks
	    peaksfile=${self_lig}_peaks/${dataname}
	    qvalue=0.1
	    echo "${macs2} callpeak -t ${self_lig} --tempdir ${self_lig}_peaks/ --nomodel --extsize 147  -g ${gsize}  -f BED -n ${peaksfile} -q ${qvalue}" >> ${s}
	    chmod 755 ${s}
            #cat ${s}
            #echo "=========="
            qsub -l h_vmem=20G -o ${s}.o -e ${s}.e ${s}
        done < ${metadata_samples}.res50000
    fi

    if [[ ${substep} == "merge_peak_sets" ]];
    then
	for qval_threshold in 1 20;
	do
	    module load bedtools/2.26.0
	    selfligation_dist=8000
            zcat -f ${DATA}/HiChIP_data/self_ligations/dist${selfligation_dist}/*peaks/*narrowPeak | awk -v qt=${qval_threshold} '{if ($9>=qt) print $0}' | cut -f1-3 | sort -k1,1 -k2,2n | uniq | bedtools merge -i stdin | awk '{print $1"\t"$2"\t"$3"\t"$2}' | gzip > ${DATA}/HiChIP_data/self_ligations/dist${selfligation_dist}/mergedPeaks.q${qval_threshold}.bed.gz
	    echo "done"
	done
    fi

    if [[ ${substep} == "assign_reads_to_peaks" ]];
    then
	selfligation_dist=8000
	while read line
        do
            read -a items <<< "$line"
            samplename=$(echo ${items[0]} | sed 's/_res50000//g')
            dataname=$(echo ${samplename} | sed 's/[.]reads[.]gz//g')
            samplefile=${items[1]}
            validPairs=${DATA}/HiChIP_data/merged_techreps/${samplename}
	    all_reads_bedpe=${DATA}/HiChIP_data/merged_techreps/${dataname}.allReads.gz
	    s=${all_reads_bedpe}.sh
	    echo "module load bedtools/2.26.0" > ${s}
	    ####TODO: remove chr21 part
	    echo "zcat -f ${validPairs} | grep chr21 | awk '{if ("'$'"3=="'$'"7) print "'$'"3\"\t\"("'$'"4-37)\"\t\"("'$'"4+38)\"\t\""'$'"7\"\t\"("'$'"8-37)\"\t\"("'$'"8+38)\"\tNA\tNA\"}' | bedtools slop -b 0 -i stdin -g ${chrSizes} | gzip > ${all_reads_bedpe}" >> ${s}
	    #qsub -o ${s}.o -e ${s}.e ${s}
	    for qval_thresh in 1 20;
	    do
		for method in 0_for_nonoverlapping_peaks all_reads_per_peak;
		do
		    if [[ ${method} == "0_for_nonoverlapping_peaks" ]];
		    then
			mkdir -p ${DATA}/HiChIP_data/merged_techreps/${method}
		        #keep only reads that fall in the peaks for this sample
			sample_peaks=${DATA}/HiChIP_data/self_ligations/dist${selfligation_dist}/${dataname}.self_lig.gz_peaks/${dataname}_peaks.narrowPeak
			cur_peaks=${sample_peaks}.q${qval_thresh}.gz
			zcat -f ${sample_peaks} | awk -v qt=${qval_thresh} '{if ($9>=qt) print $0}' | gzip > ${cur_peaks}
			out_bedpe=${DATA}/HiChIP_data/merged_techreps/${method}/${dataname}.q${qval_thresh}.bedpe.gz
			s=${out_bedpe}.sh
			reads_keep=${DATA}/HiChIP_data/merged_techreps/${method}/${dataname}.mergedPeaks.q${qval_thresh}.bedpe.gz
			contact_map=${DATA}/HiChIP_data/merged_techreps/${method}/${dataname}.q${qval_thresh}.contactMap.gz
			echo "module load bedtools/2.26.0" > ${s}
			echo "${MYCODE}/genome_utils/3Dutils/translate_bedpe.sh ${all_reads_bedpe} ${cur_peaks} ${out_bedpe} 0" >> ${s}
			echo "${MYCODE}/genome_utils/3Dutils/translate_bedpe.sh ${out_bedpe} ${DATA}/HiChIP_data/self_ligations/dist${selfligation_dist}/mergedPeaks.q${qval_thresh}.bed.gz ${reads_keep} 0" >> ${s}
			echo "zcat -f ${reads_keep} | cut -f1,2,4,5 | awk '{print "'$'"1\"_\""'$'"2\"_\""'$'"3\"_\""'$'"4}' | awk '{count["'$'"1]++} END {for (word in count) print word\"\t\"count[word]}' | sed 's/_/\t/g' | gzip > ${contact_map}" >> ${s}
			echo "rm ${out_bedpe} ${reads_keep}" >> ${s}
			chmod 755 ${s}
		        qsub -o ${s}.o -e ${s}.e ${s}
		    fi

		    if [[ ${method} == "all_reads_per_peak" ]];
		    then
		        #keep all reads
			echo "coming soon"
		    fi
		done
	    done
	done < ${metadata_samples}.res50000
    fi

    if [[ ${substep} == "zero_metadata" ]];
    then
	for qval_thresh in 1 20;
	do
	    #samples
	    zcat -f ${metadata_samples}.res50000 | sed 's/[.]reads[.]gz_res50000//g' | cut -f1 | awk -v dir=${DATA}/HiChIP_data/merged_techreps/0_for_nonoverlapping_peaks -v qt=${qval_thresh} '{print $1"\t"dir"/"$1".q"qt".contactMap.gz"}' > ${metadata_samples}.q${qval_thresh}.0_for_nonoverlapping_peaks
	    #pairs
	    zcat -f ${metadata_pairs}.res50000 | sed 's/[.]reads[.]gz_res50000//g' > ${metadata_pairs}.q${qval_thresh}.0_for_nonoverlapping_peaks
	    echo ${metadata_pairs}
	done
    fi

    if [[ ${substep} == "zero_split" ]];
    then
	selfligation_dist=8000
	for qval_thresh in 1 20;
        do
	    out=${DATA}/results/HiChIP/0_for_nonoverlapping_peaks.q${qval_thresh}.keepdiag.transition
	    bins=${DATA}/HiChIP_data/self_ligations/dist${selfligation_dist}/mergedPeaks.q${qval_thresh}.bed.gz
            ${mypython} ${MYCODE}/3DChromatin_ReplicateQC/3DChromatin_ReplicateQC.py split --metadata_samples ${metadata_samples}.q${qval_thresh}.0_for_nonoverlapping_peaks --bins ${bins} --outdir ${out} --methods GenomeDISCO,HiCRep,HiC-Spector --running_mode sge
	done
    fi

    if [[ ${substep} == "zero_run" ]];
    then
	for qval_thresh in 1 20;
        do
	    out=${DATA}/results/HiChIP/0_for_nonoverlapping_peaks.q${qval_thresh}.keepdiag.transition
            ${mypython} ${MYCODE}/3DChromatin_ReplicateQC/3DChromatin_ReplicateQC.py reproducibility --metadata_pairs ${metadata_pairs}.q${qval_thresh}.0_for_nonoverlapping_peaks --outdir ${out} --methods GenomeDISCO --parameters_file ${MYCODE}/3DChromatin_ReplicateQC/examples/example_parameters.bystep.10steps.transition.txt --subset_chromosomes chr21 --concise_analysis --running_mode sge
        done
    fi

    if [[ ${substep} == "zero_compile_scores_transition" ]];
    then
	for qval_thresh in 1 20;
        do
	    d=${DATA}/results/HiChIP/0_for_nonoverlapping_peaks.q${qval_thresh}.keepdiag.transition
            mkdir -p ${d}/compiled_scores
            for chromo in 21;
            do
		zcat -f ${d}/results/reproducibility/GenomeDISCO/chr${chromo}.*.scoresByStep.txt | grep -v m1 > ${d}/compiled_scores/chr${chromo}.GenomeDISCO.scores.txt
		zcat -f ${d}/results/reproducibility/HiCRep/chr${chromo}.*.scores.txt > ${d}/compiled_scores/chr${chromo}.HiCRep.scores.txt
            zcat -f ${d}/results/reproducibility/HiC-Spector/chr${chromo}.*.scores.txt > ${d}/compiled_scores/chr${chromo}.HiC-Spector.scores.txt
            done
	done
    fi

    if [[ ${substep} == "compile_scores" ]];
    then
        mkdir -p ${DATA}/results/HiChIP/res${res}/compiled_scores
        for chromo in 21;
        do
            zcat -f ${DATA}/results/HiChIP/res${res}/results/reproducibility/GenomeDISCO/chr${chromo}.*.scoresByStep.txt | grep -v m1 > ${DATA}/results/HiChIP/res${res}/compiled_scores/chr${chromo}.GenomeDISCO.scores.txt
            zcat -f ${DATA}/results/HiChIP/res${res}/results/reproducibility/HiCRep/chr${chromo}.*.scores.txt > ${DATA}/results/HiChIP/res${res}/compiled_scores/chr${chromo}.HiCRep.scores.txt
            zcat -f ${DATA}/results/HiChIP/res${res}/results/reproducibility/HiC-Spector/chr${chromo}.*.scores.txt > ${DATA}/results/HiChIP/res${res}/compiled_scores/chr${chromo}.HiC-Spector.scores.txt
        done
    fi

    if [[ ${substep} == "compile_scores_keepDiag" ]];
    then
	d=${DATA}/results/HiChIP/res${res}_keepDiag
        mkdir -p ${d}/compiled_scores
        for chromo in 21;
        do
            zcat -f ${d}/results/reproducibility/GenomeDISCO/chr${chromo}.*.scoresByStep.txt | grep -v m1 > ${d}/compiled_scores/chr${chromo}.GenomeDISCO.scores.txt
            zcat -f ${d}/results/reproducibility/HiCRep/chr${chromo}.*.scores.txt > ${d}/compiled_scores/chr${chromo}.HiCRep.scores.txt
            zcat -f ${d}/results/reproducibility/HiC-Spector/chr${chromo}.*.scores.txt > ${d}/compiled_scores/chr${chromo}.HiC-Spector.scores.txt
        done
    fi

    if [[ ${substep} == "compile_scores_transition" ]];
    then
        d=${DATA}/results/HiChIP/res${res}_transition
        mkdir -p ${d}/compiled_scores
        for chromo in 21;
        do
            zcat -f ${d}/results/reproducibility/GenomeDISCO/chr${chromo}.*.scoresByStep.txt | grep -v m1 > ${d}/compiled_scores/chr${chromo}.GenomeDISCO.scores.txt
            zcat -f ${d}/results/reproducibility/HiCRep/*txt | grep "chr"${chromo} | cut -f1,2,4 > ${d}/compiled_scores/chr${chromo}.HiCRep.scores.txt
            zcat -f ${d}/results/reproducibility/HiC-Spector/*.txt | grep "chr"${chromo} | cut -f1,2,4> ${d}/compiled_scores/chr${chromo}.HiC-Spector.scores.txt
        done
    fi


    #call peaks using simple macs
    #compare peaks called with the chip-seq
    #re-bin reads by peaks
    #re-run GenomeDISCO

fi