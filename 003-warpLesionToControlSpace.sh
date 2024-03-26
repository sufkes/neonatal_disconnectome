#!/bin/bash

# Warp lesion maps in 40w template space to control subject spaces.

#input_dir='/arc/burst/st-smiller6-1/users/sufkes/disconnectome_dhcp/input'
control_dir='/arc/burst/st-smiller6-1/users/sufkes/disconnectome_dhcp/controls'
runs_dir='/arc/burst/st-smiller6-1/users/sufkes/disconnectome_dhcp/runs'

while read lesion_subject_run_dir; do # Loop over lesions subjects.
    lesion_subject="$(basename "$lesion_subject_run_dir")"

    lesion_40w_path="${lesion_subject_run_dir}/template_space/40w/lesion.nii.gz"

    while read control_session_dir; do # Loop over control subjects.	
	control_subject_dir="$(realpath "${control_session_dir}/..")"
	
	control_subject="$(basename "$control_subject_dir")"
	control_session="$(basename "$control_session_dir")"
	
	reference_path="${control_session_dir}/dwi/${control_subject}_${control_session}_desc-brain_mask.nii.gz" # image in control DWI space
	warp_path="${control_session_dir}/xfm/${control_subject}_${control_session}_from-extdhcp40wk_to-dwi_mode-image.nii.gz"

	out_dir="${runs_dir}/${lesion_subject}/control_space/${control_subject}_${control_session}"
	mkdir -p "$out_dir"

	out_name='lesion.nii.gz'
	out_path="${out_dir}/${out_name}"
	
	qsub <<EOF
#PBS -l walltime=01:00:00,select=1:ncpus=1:mem=16gb
#PBS -N "applywarp-${lesion_subject}_to_${control_subject}_${control_session}"
#PBS -A st-smiller6-1
#PBS -m n
#PBS -j oe
#PBS -o "$out_dir"

source /arc/project/st-smiller6-1/tools/shared_envs/py3

applywarp -i "$lesion_40w_path" -o "$out_path" -r "$reference_path" -w "$warp_path" --interp=nn

EOF
    done < <(find "$control_dir" -mindepth 2 -maxdepth 2 -type d | sort)
done < <(find "$runs_dir" -mindepth 1 -maxdepth 1 -type d | sort)
