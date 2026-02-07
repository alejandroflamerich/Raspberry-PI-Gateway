import create from 'zustand'

type State = { token: string | null, setToken: (t: string | null) => void }

export const useAuth = create<State>((set) => ({
  token: typeof window !== 'undefined' ? window.localStorage.getItem('token') : null,
  setToken: (t) => {
    if(t) window.localStorage.setItem('token', t)
    else window.localStorage.removeItem('token')
    set({ token: t })
  }
}))
