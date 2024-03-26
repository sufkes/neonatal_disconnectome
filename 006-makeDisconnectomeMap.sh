#!/bin/bash

# Warp lesion visition maps from control spaces back to 40w template space.

#input_dir='/arc/burst/st-smiller6-1/users/sufkes/disconnectome_dhcp/input'
control_dir='/arc/burst/st-smiller6-1/users/sufkes/disconnectome_dhcp/controls'
runs_dir='/arc/burst/st-smiller6-1/users/sufkes/disconnectome_dhcp/runs'

threshold=0 # threshold probability for inclusion in disconnectome map.
for threshold in 0 0.1 0.2 0.3 0.4 0.5; do
    while read lesion_subject_run_dir; do # Loop over lesions subjects.
	lesion_subject="$(basename "$lesion_subject_run_dir")"
	
	visitation_maps_dir="${lesion_subject_run_dir}/visitation_maps_40w"
	
	# Generate list of visitation maps. Assume there are no horrible things in the path names (e.g. spaces).
	visitation_map_array=()
	while read visitation_map_path; do 
	    visitation_map_array+=("$visitation_map_path")
	done < <(find "$visitation_maps_dir" -type f -name 'visitation_map.nii.gz')
	
	out_dir="${lesion_subject_run_dir}/disconnectome"
	mkdir -p "$out_dir"
	
	out_path="${out_dir}/disconnectome-threshold_${threshold}.nii.gz"
	
	qsub <<EOF
#!/bin/bash
#PBS -l walltime=01:00:00,select=1:ncpus=1:mem=16gb
#PBS -N "makeDisconnectomeMap-${lesion_subject}"
#PBS -A st-smiller6-1
#PBS -m n
#PBS -j oe
#PBS -o "$out_dir"

source /arc/project/st-smiller6-1/tools/shared_envs/py3

makeDisconnectomeMap.py -i ${visitation_map_array[@]} -o "$out_path" -t "$threshold"

EOF
    done < <(find "$runs_dir" -mindepth 1 -maxdepth 1 -type d | sort)
done
