# Tab UI Contract

The tab strip displays stable tab identity, title, active state and lock state.

UI controls may request tab operations, but persistence and identity remain owned by the browser state/persistence layer.

A disabled close control is not a substitute for the lock invariant; the close operation must enforce the invariant too.