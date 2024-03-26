#!/bin/bash

# Warp lesion visition maps from control spaces back to 40w template space.

#input_dir='/arc/burst/st-smiller6-1/users/sufkes/disconnectome_dhcp/input'
control_dir='/arc/burst/st-smiller6-1/users/sufkes/disconnectome_dhcp/controls'
runs_dir='/arc/burst/st-smiller6-1/users/sufkes/disconnectome_dhcp/runs'

while read lesion_subject_run_dir; do # Loop over lesions subjects.
    lesion_subject="$(basename "$lesion_subject_run_dir")"

    while read control_session_dir; do # Loop over control subjects.	
	control_subject_dir="$(realpath "${control_session_dir}/..")"
	
	control_subject="$(basename "$control_subject_dir")"
	control_session="$(basename "$control_session_dir")"
	
	lesion_in_control_space_dir="${runs_dir}/${lesion_subject}/control_space/${control_subject}_${control_session}"

	visitation_map_path="${lesion_in_control_space_dir}/visitation_map.nii.gz"

	template_40w_path='/arc/burst/st-smiller6-1/users/sufkes/disconnectome_dhcp/template/templates/week40_T1w.nii.gz'

	control_to_template_40w_warp_path="${control_session_dir}/xfm/${control_subject}_${control_session}_from-dwi_to-extdhcp40wk_mode-image.nii.gz"

	out_dir="${lesion_subject_run_dir}/visitation_maps_40w/${control_subject}_${control_session}"
	mkdir -p "$out_dir"
	
	out_name="visitation_map.nii.gz"
	out_path="${out_dir}/${out_name}"
	
	qsub <<EOF
#!/bin/bash
#PBS -l walltime=01:00:00,select=1:ncpus=1:mem=16gb
#PBS -N "warp_visitation_maps_to_40w_template-${lesion_subject}_in_${control_subject}_${control_session}"
#PBS -A st-smiller6-1
#PBS -m n
#PBS -j oe
#PBS -o "$out_dir"

source /arc/project/st-smiller6-1/tools/shared_envs/py3

applywarp -i "$visitation_map_path" -o "$out_path" -r "$template_40w_path" -w "$control_to_template_40w_warp_path" --interp=trilinear

EOF
    done < <(find "$control_dir" -mindepth 2 -maxdepth 2 -type d | sort)
done < <(find "$runs_dir" -mindepth 1 -maxdepth 1 -type d | sort)
