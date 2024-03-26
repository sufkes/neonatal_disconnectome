#!/bin/bash

# Filter tractograms to show only tracts which pass through each the lesion.

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
	lesion_path="${lesion_in_control_space_dir}/lesion.nii.gz"

	track_path="${control_dir}/${control_subject}/${control_session}/odf_tracker/${control_subject}_${control_session}_hardi.trk"

	visitation_map_path="${lesion_in_control_space_dir}/visitation_map.nii.gz"
	
	qsub <<EOF
#!/bin/bash
#PBS -l walltime=01:00:00,select=1:ncpus=1:mem=16gb
#PBS -N "filter_tracts-${lesion_subject}_in_${control_subject}_${control_session}"
#PBS -A st-smiller6-1
#PBS -m n
#PBS -j oe
#PBS -o "$lesion_in_control_space_dir"

source /arc/project/st-smiller6-1/tools/shared_envs/py3

track_vis "$track_path" --roi "$lesion_path" --output_volume "$visitation_map_path" --do_not_render

EOF
    done < <(find "$control_dir" -mindepth 2 -maxdepth 2 -type d | sort)
done < <(find "$runs_dir" -mindepth 1 -maxdepth 1 -type d | sort)
