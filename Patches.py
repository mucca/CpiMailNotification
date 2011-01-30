from Products.DCWorkflow.DCWorkflow import DCWorkflowDefinition
from Products.DCWorkflow.Expression import StateChangeInfo
from Products.DCWorkflow.Expression import createExprContext
from Acquisition import aq_inner
from Acquisition import aq_parent
from Products.CMFCore.WorkflowCore import WorkflowException
import pdb


def patch(klass, method):
    mid = method.__name__
    ori_mid = '_original_' + mid
    if not hasattr(klass, ori_mid):
        setattr(klass, ori_mid, getattr(klass, mid))
    setattr(klass, mid, method)

def _executeTransition(self, ob, tdef=None, kwargs=None):
    '''
    Private method.
    Puts object in a new state.
    '''
    sci = None
    econtext = None
    moved_exc = None

    # Figure out the old and new states.
    old_sdef = self._getWorkflowStateOf(ob)
    old_state = old_sdef.getId()
    if tdef is None:
        new_state = self.initial_state
        former_status = {}
    else:
        new_state = tdef.new_state_id
        if not new_state:
            # Stay in same state.
            new_state = old_state
        former_status = self._getStatusOf(ob)
    new_sdef = self.states.get(new_state, None)
    if new_sdef is None:
        raise WorkflowException, (
            'Destination state undefined: ' + new_state)

    # Execute the "before" script.
    if tdef is not None and tdef.script_name:
        script = self.scripts[tdef.script_name]
        # Pass lots of info to the script in a single parameter.
        sci = StateChangeInfo(
            ob, self, former_status, tdef, old_sdef, new_sdef, kwargs)
        try:
            script(sci)  # May throw an exception.
        except ObjectMoved, moved_exc:
            ob = moved_exc.getNewObject()
            # Re-raise after transition

    # Update variables.
    state_values = new_sdef.var_values
    if state_values is None: state_values = {}
    tdef_exprs = None
    if tdef is not None: tdef_exprs = tdef.var_exprs
    if tdef_exprs is None: tdef_exprs = {}
    status = {}
    for id, vdef in self.variables.items():
        if not vdef.for_status:
            continue
        expr = None
        if state_values.has_key(id):
            value = state_values[id]
        elif tdef_exprs.has_key(id):
            expr = tdef_exprs[id]
        elif not vdef.update_always and former_status.has_key(id):
            # Preserve former value
            value = former_status[id]
        else:
            if vdef.default_expr is not None:
                expr = vdef.default_expr
            else:
                value = vdef.default_value
        if expr is not None:
            # Evaluate an expression.
            if econtext is None:
                # Lazily create the expression context.
                if sci is None:
                    sci = StateChangeInfo(
                        ob, self, former_status, tdef,
                        old_sdef, new_sdef, kwargs)
                econtext = createExprContext(sci)
            value = expr(econtext)
        status[id] = value

    # Update state.
    status[self.state_var] = new_state
    tool = aq_parent(aq_inner(self))
    tool.setStatusOf(self.id, ob, status)

    # notify the transition of the state 
    if hasattr(ob,"mailnotification_tool"):
        ob.mailnotification_tool.stateTransationNotify(sci)

    # Update role to permission assignments.
    self.updateRoleMappingsFor(ob)

    # Execute the "after" script.
    if tdef is not None and tdef.after_script_name:
        script = self.scripts[tdef.after_script_name]
        # Pass lots of info to the script in a single parameter.
        sci = StateChangeInfo(
            ob, self, status, tdef, old_sdef, new_sdef, kwargs)
        script(sci)  # May throw an exception.
    
    # Return the new state object.
    if moved_exc is not None:
        # Propagate the notification that the object has moved.
        raise moved_exc
    else:
        return new_sdef

patch(DCWorkflowDefinition,_executeTransition)