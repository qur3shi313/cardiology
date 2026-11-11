"""Continue the next authored episodes in a single local picture queue."""
import subprocess
import sys


def main():
    queue=(('aftercare',),('pci',),('coating',),('restenosis',),('post_pci',),
           ('pressure',),('imaging',),('calcium',),('emergency','14'),('emergency','15'),
           ('structural','17'),('valve_implant',),('structural','19'),('structural','20'))
    blocked=[]
    for name,*arguments in queue:
        print(f'Preparing scenes with {name} {" ".join(arguments)}',flush=True)
        result=subprocess.run([sys.executable,'-u','-m',f'elysian_video.{name}',*arguments])
        if result.returncode:
            print(f'{name} stopped at its saved scene files',flush=True)
            blocked.append((name,arguments))
    if blocked:
        print(f'Resume blocked picture sections: {blocked}',flush=True)
    return int(bool(blocked))


if __name__=='__main__':
    raise SystemExit(main())
