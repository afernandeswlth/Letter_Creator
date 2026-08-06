import type { LetterTypeId } from '~/types'

export type ThemeName = 'blue' | 'green' | 'purple'

// The dashboard groups letters by team colour, but every letter's *form* pages
// use a single blue scheme (as before). Map all types to blue here; change an
// entry to 'green'/'purple' to theme that letter's form pages by team instead.
export const THEME_OF: Record<LetterTypeId, ThemeName> = {
  'pre-approval': 'blue',
  'conditional-approval': 'blue',
  approval: 'blue',
  welcome: 'blue',
  commencement: 'blue',
  discharge: 'blue',
  custom: 'blue',
}

export interface ThemeClasses {
  wash: string // page background tint for the letter's form pages
  btn: string // primary action button
  title: string // letter-type heading colour
  stepActive: string // wizard stepper — current step
  stepDone: string // wizard stepper — completed step
}

// Full class strings (so Tailwind's JIT keeps them) keyed by theme.
export const THEME_CLASSES: Record<ThemeName, ThemeClasses> = {
  blue: {
    wash: 'bg-gradient-to-b from-blue-50 to-white',
    btn: 'bg-blue-600 hover:bg-blue-700',
    title: 'text-blue-700',
    stepActive: 'bg-blue-600 text-white',
    stepDone: 'bg-blue-100 text-blue-700',
  },
  green: {
    wash: 'bg-gradient-to-b from-emerald-50 to-white',
    btn: 'bg-emerald-600 hover:bg-emerald-700',
    title: 'text-emerald-700',
    stepActive: 'bg-emerald-600 text-white',
    stepDone: 'bg-emerald-100 text-emerald-700',
  },
  purple: {
    wash: 'bg-gradient-to-b from-violet-50 to-white',
    btn: 'bg-violet-600 hover:bg-violet-700',
    title: 'text-violet-700',
    stepActive: 'bg-violet-600 text-white',
    stepDone: 'bg-violet-100 text-violet-700',
  },
}

export function themeName(id: LetterTypeId | null | undefined): ThemeName {
  return (id && THEME_OF[id]) || 'blue'
}
