#!/usr/bin/env node

/**
 * Skill Profile Activator
 * Manages Claude Code skill profiles via symlinks
 *
 * Usage:
 *   node activate-profile.js [profile1] [profile2] ...
 *   node activate-profile.js --list
 *   node activate-profile.js --show
 *
 * Examples:
 *   node activate-profile.js core quality
 *   node activate-profile.js all
 */

const fs = require('fs');
const path = require('path');

// ANSI colors for terminal output
const colors = {
  reset: '\x1b[0m',
  blue: '\x1b[34m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m'
};

// Determine directory locations
// By default, looks for skill-profiles/ and skills/ relative to this script
const scriptDir = __dirname;
const claudeDir = process.env.CLAUDE_DIR || path.join(process.env.HOME, '.claude');
const profilesDir = path.join(claudeDir, 'skill-profiles');
const skillsDir = path.join(claudeDir, 'skills');

function print(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function getAvailableProfiles() {
  try {
    const entries = fs.readdirSync(profilesDir, { withFileTypes: true });
    return entries
      .filter(entry => entry.isDirectory())
      .map(entry => entry.name)
      .filter(name => !name.startsWith('.'));
  } catch (error) {
    print(`Error reading profiles directory: ${error.message}`, 'red');
    return [];
  }
}

function getProfileSkills(profileName) {
  const profilePath = path.join(profilesDir, profileName);
  try {
    const entries = fs.readdirSync(profilePath, { withFileTypes: true });
    return entries
      .filter(entry => !entry.name.startsWith('.'))
      .map(entry => ({ name: entry.name }));
  } catch (error) {
    return [];
  }
}

function createSymlink(target, linkPath) {
  try {
    if (fs.existsSync(linkPath)) {
      const stats = fs.lstatSync(linkPath);
      if (stats.isSymbolicLink() || stats.isFile()) {
        fs.unlinkSync(linkPath);
      }
    }

    const relativePath = path.relative(path.dirname(linkPath), target);
    fs.symlinkSync(relativePath, linkPath, 'junction');
    return true;
  } catch (error) {
    try {
      if (fs.statSync(target).isDirectory()) {
        fs.cpSync(target, linkPath, { recursive: true });
      } else {
        fs.copyFileSync(target, linkPath);
      }
      return true;
    } catch (copyError) {
      print(`  Warning: Failed to link ${path.basename(linkPath)}: ${error.message}`, 'yellow');
      return false;
    }
  }
}

function clearSkills() {
  try {
    if (!fs.existsSync(skillsDir)) {
      fs.mkdirSync(skillsDir, { recursive: true });
      return;
    }

    const entries = fs.readdirSync(skillsDir, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.name.startsWith('.')) continue;
      const entryPath = path.join(skillsDir, entry.name);
      const stats = fs.lstatSync(entryPath);
      if (stats.isSymbolicLink()) {
        fs.unlinkSync(entryPath);
      } else if (stats.isDirectory()) {
        fs.rmSync(entryPath, { recursive: true, force: true });
      }
    }
  } catch (error) {
    print(`Error clearing skills: ${error.message}`, 'red');
  }
}

function activateProfile(profileName) {
  const profilePath = path.join(profilesDir, profileName);

  if (!fs.existsSync(profilePath)) {
    print(`Warning: Profile '${profileName}' not found`, 'yellow');
    return 0;
  }

  print(`Activating profile: ${profileName}`, 'green');

  const skills = getProfileSkills(profileName);
  let activatedCount = 0;

  for (const skill of skills) {
    const sourcePath = path.join(profilePath, skill.name);
    const targetPath = path.join(skillsDir, skill.name);

    if (createSymlink(sourcePath, targetPath)) {
      print(`  + ${skill.name}`, 'reset');
      activatedCount++;
    }
  }

  return activatedCount;
}

function getCurrentActivation() {
  if (!fs.existsSync(skillsDir)) {
    return { skills: [], profileCounts: {} };
  }

  const skills = [];
  const profileCounts = {};

  try {
    const entries = fs.readdirSync(skillsDir, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.name.startsWith('.')) continue;
      const skillPath = path.join(skillsDir, entry.name);
      const stats = fs.lstatSync(skillPath);

      if (stats.isSymbolicLink()) {
        skills.push(entry.name);
        try {
          const target = fs.readlinkSync(skillPath);
          const match = target.match(/skill-profiles[/\\]([^/\\]+)[/\\]/);
          if (match) {
            const profile = match[1];
            profileCounts[profile] = (profileCounts[profile] || 0) + 1;
          }
        } catch (err) { /* broken symlink */ }
      }
    }
  } catch (error) {
    print(`Error reading current activation: ${error.message}`, 'red');
  }

  return { skills, profileCounts };
}

function listProfiles() {
  print('\n=== Available Profiles ===', 'blue');
  print('');

  const profiles = getAvailableProfiles();
  const current = getCurrentActivation();

  if (profiles.length === 0) {
    print('Warning: No profiles found in skill-profiles/', 'yellow');
    return;
  }

  print('Profile Name          Skills  Status', 'reset');
  print('-'.repeat(60), 'reset');

  profiles.forEach(profile => {
    const skills = getProfileSkills(profile);
    const isActive = current.profileCounts[profile] > 0;
    const activeCount = current.profileCounts[profile] || 0;

    const nameCol = profile.padEnd(20);
    const countCol = skills.length.toString().padEnd(6);
    const status = isActive ? `Active (${activeCount} skills)` : '';
    const color = isActive ? 'green' : 'reset';

    print(`${nameCol} ${countCol}  ${status}`, color);
  });

  print('');
  print(`Total profiles: ${profiles.length}`, 'reset');
}

function showCurrent() {
  print('\n=== Current Profile Activation ===', 'blue');
  print('');

  const { skills, profileCounts } = getCurrentActivation();

  if (Object.keys(profileCounts).length === 0) {
    print('Warning: No profiles currently activated', 'yellow');
    print('');
    print('To activate profiles:', 'reset');
    print('  node activate-profile.js <profile1> <profile2> ...', 'reset');
    print('');
    return;
  }

  print('Activated Profiles:', 'reset');
  Object.entries(profileCounts)
    .sort((a, b) => b[1] - a[1])
    .forEach(([profile, count]) => {
      print(`  ${profile.padEnd(20)} ${count} skills`, 'green');
    });

  print('');
  print(`Total activated skills: ${skills.length}`, 'blue');

  const contextEstimate = (skills.length * 1.5).toFixed(1);
  print(`Estimated context usage: ~${contextEstimate}K tokens`, 'reset');
  print('');
}

function showUsage() {
  print('\n=== Skill Profile Activator ===', 'blue');

  const profiles = getAvailableProfiles();

  if (profiles.length === 0) {
    print('\nWarning: No profiles found in skill-profiles/', 'yellow');
    return;
  }

  print('\nAvailable profiles:', 'yellow');
  profiles.forEach(profile => {
    const skills = getProfileSkills(profile);
    print(`  ${profile} (${skills.length} skills)`, 'reset');
  });

  print('\nUsage:', 'reset');
  print('  node activate-profile.js <profile1> [profile2] ...', 'reset');
  print('  node activate-profile.js --list    # List all profiles', 'reset');
  print('  node activate-profile.js --show    # Show current activation', 'reset');
  print('');
}

function main() {
  const args = process.argv.slice(2);

  if (args.includes('--list') || args.includes('-l')) {
    listProfiles();
    process.exit(0);
  }

  if (args.includes('--show') || args.includes('-s')) {
    showCurrent();
    process.exit(0);
  }

  if (args.length === 0) {
    showUsage();
    process.exit(0);
  }

  print('\n=== Skill Profile Activator ===', 'blue');
  print('');

  if (!fs.existsSync(skillsDir)) {
    fs.mkdirSync(skillsDir, { recursive: true });
  }

  print('Clearing existing skill symlinks...', 'yellow');
  clearSkills();
  print('');

  let totalActivated = 0;
  for (const profile of args) {
    const count = activateProfile(profile);
    totalActivated += count;
    print('');
  }

  print(`Activated ${totalActivated} skills from ${args.length} profile(s)`, 'green');
  print('');
  print('Active profiles: ' + args.join(', '), 'reset');
  print('');

  const availableProfiles = getAvailableProfiles();
  let totalSkills = 0;
  for (const profile of availableProfiles) {
    totalSkills += getProfileSkills(profile).length;
  }

  if (totalSkills > 0) {
    const efficiency = ((totalSkills - totalActivated) / totalSkills * 100).toFixed(1);
    print(`Context efficiency: ${efficiency}% (${totalActivated}/${totalSkills} skills loaded)`, 'blue');
    print('');
  }
}

if (require.main === module) {
  main();
}

module.exports = { activateProfile, getAvailableProfiles, clearSkills };
