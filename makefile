deploy:
	ssh hyperion "cd parole-de-robot && git pull"
	rsync -avz .streamlit hyperion:parole-de-robot
	ssh hyperion "systemctl --user restart cesia.service"
