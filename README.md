# Philosophy

The objective of these skills is to work along with the matt-pocock skills to build and maintain a
wiki about the files in your project repo. When the agent is resolving requests about your project
files, it consults the wiki files first, to figure out how things in your repo work and what files
are relevant to look at in more detail to answer your questions. Without a wiki like this, every
new prompt in your project has to load into the context a large number of files and it may still
miss some files in the process. The wiki makes it faster and more reliable. 

So you can choose how to update the wiki:
- Manually run /wiki-update after you've made significant changes (I prefer this one)
- Make a commit hook that automatically runs a update before each commit
- Have it triggered automatically as a github action when a new merge into main has occurred
- Have it triggered by another skill as part of a workflow

After implementing a ticket, you may run the /approved skill to commit, push, and /wiki-update your
project. Every so often you should run a /wiki-lint to check standards and consistency in the wiki.

# Notes

- The WIKI-SCHEMA.md file gets copied from the sourcery repo to your project. It contains
  information about how the wiki is to be maintained. Generally you shuold not modify it, but if you
  find a need to, and you want it to last for future projects, you should raise a PR to the
  sourcery repo with that change. When you pull updates from the sourcery repo and run the setup
  skill, it will replace your SCHEMA file with what's in the repo. This file gets loaded into the
  context only when needed (most wiki skills will need it).
- Use AGENTS.md for local settings that apply to every prompt. The setup adds a couple sections to
  it but otherwise will leave your changes alone. 

# Setup

## 1. Clone the repo
``` bash
# Something like:
git clone http://127.0.0.1:3001/zarisoft/sourcery.git
cd sourcery
```

## 2. Remove the old wiki skills if you have them, since they now conflict
``` bash
rm -rf ~/.pi/agent/skills/wiki-*
```

These new skills don't have all of the features of the old wiki skills yet, but it has the ones we 
mostly used, and will have the rest soon.

## 3. Link the skills into your pi skills folder (or whatever harness you are using):
``` bash
# Put this function in your shell profile so you can use it easily
link_pi_skills() {
  local folder \
    pi_skills_path=~/.pi/agent/skills \
    skill \
    target \

  for folder in $*; do
    folder=$(realpath $folder) || return 1
    for skill in $folder/*; do
      skill=${skill##*/}
      if [[ $skill == *.* ]]; then
        continue
      fi
      target=$pi_skills_path/$skill
      if [[ -e $target ]]; then
        echo "rm -rf $target" || return 1
        rm -rf $target || return 1
      fi
      echo "ln -s $folder/$skill $target"
      ln -s $folder/$skill $target || return 1
    done
  done
}

# While in the sourcery folder:
link_pi_skills skills

```

By linking them instead of copying, whenever you do a pull on the skills repo, it will 
automatically update the pi skills also. You could also just copy them of course, but 
then you lose this easy to update mechanism. 

## 4. Go to your project repo you want to use these skills on, and start pi.
``` bash
cd /some/cool/project
pi
```

## 5. Run the setup skill in pi:
```
/skill:sourcery-setup
```

This can be run multiple times safely, and it will replace the created files each time. This is 
important if you want to update the repo, because some files are copied from the skill into the 
repo itself. So to cleanly update the sourcery repo, do a pull there, then go to pi in your 
project repo, and run the setup skill again, and it will take care of the rest. 

## 6. Follow the instructions of the setup skill

## 7. Understand how it works. 

This works a little differently than the other tools. 
* It is meant to work smoothly alongside of the matt-pocock skills, so you should install those also.
  You can use the same link_pi_skills function on those also. 
* It has two sections of information, the wiki, and the source material.
  EVERYTHING outside of the /wiki folder in your repo is part of the source material, and will be
  ingested into the wiki. 
* It is meant to automatically turn all queries about your source material into wiki lookups, no 
  special skill needed. 

## 8. Create the new wiki pages.

```
/skill:wiki-update
```

It will branch into 3 subagents by default and tackle your entire repo. You can adjust the number 
of subagents in your AGENTS.md file. That is where most repo local settings/instructions should be 
placed. It *should* automatically detect at least some of the outdated wiki pages and upgrade them
automatically to the new standard. But to clean up old wiki pages completely, you can run the lint:

```
/skill:wiki-lint
```

which should convert all of the old pages to the new OKF standard. 

When you make changes to your source material, just run wiki-update again before you commit. It 
will use git logs to automatically determine exactly what files have changed since the wiki was
last updated and only focus on those. 

## 9. Go ahead and continue your coding / research analysis. 

The wiki should automatically be consulted as needed when agents are trying to understand where
something is happening in the code or answer deep research questions about large documents. 
I still recommend keeping source documents from being too big, for the sake of efficiency. Use
AI to break large documents down into chapter size pieces. Many docs already have chapters, but
if they don't I'm sure a decent AI model can figure it out. 

# Not yet done, but will be soon:

* Will make an /approved skill that you use after the /implement skill and have reviewed the
  changes. The approved skill will commit and push the changes, close the ticket, and update
  the wiki.
* Will add the audit skill. This is a much deeper review of a document to validate it's information.

