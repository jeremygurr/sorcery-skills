# Setup

## 1. Clone the repo
``` bash
# Something like:
git clone http://127.0.0.1:3001/zarisoft/wizard-skills.git
cd wizard-skills
```

## 2. Link the skills into your pi skills folder (or whatever harness you are using):
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

# While in the wizard-skills folder:
link_pi_skills skills
```

## 3. Go to your project repo you want to use these skills on.

## 4. Run the setup skill in pi:
```
/skill:setup-wizard-skills
```

## 5. Follow the instructions of the setup skill

## 6. Understand how it works. 

This works a little differently than the other tools. 
* It is meant to work smoothly alongside of the matt-pocock skills, so you should install those also.
  You can use the same link_pi_skills function on those also. 
* It has two sections of information, the wiki, and the source material.
  EVERYTHING outside of the /wiki folder in your repo is part of the source material, and will be
  ingested into the wiki. 
* It is meant to automatically turn all queries about your source material into wiki lookups, no 
  special skill needed. 
* It does NOT use the old wiki-skills, and it does conflict with them. So you'll need to remove them
  if you have them installed. 

## 7. Create the new wiki pages.

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

## 8. Go ahead and continue your coding / research analysis. 

The wiki should automatically be consulted as needed when agents are trying to understand where
something is happening in the code or answer deep research questions about large documents. 
I still recommend keeping source documents from being too big, for the sake of efficiency. Use
AI to break large documents down into chapter size pieces. Many docs already have chapters, but
if they don't I'm sure a decent AI model can figure it out. 

# Not yet done, but will be soon:

* Will make an "approved" skill that you use after the /implement skill and have reviewed the
  changes. The approved skill will commit and push the changes, close the ticket, and update
  the wiki.
* Will add the split/merge wiki skills. This is needed for long term maintenance of large wiki
  libraries. 
* Will add the audit skill. This is a much deeper review of a document to validate it's information.
