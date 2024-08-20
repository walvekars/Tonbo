"""In 1st server action perform this 2 server action (confirm all) """
"""
Step 1
create backorder
"""

if record.product_qty == 1:
    raise UserError("Quantity should be more than one to Produce All.")

bom = record.bom_id.id
count = 2
main_rec = record

# procurement_group_id = env["procurement.group"].create({'name': main_rec.name})
# record.write({
#   'procurement_group_id' : procurement_group_id.id
# })
for r in range(1, int(record.product_qty)):
    rec_copy = record.copy(default={
        'name': f'{record.name}-{count}',
        'product_qty': 1,
        'procurement_group_id': record.procurement_group_id.id,
        'bom_id': False,
        'move_raw_ids': False,
        'origin': record.origin
    })
    rec_copy['bom_id'] = bom
    #   # rec_copy.write({
    #   #   'bom_id' :bom,
    #   # })
    rec_copy._onchange_move_raw()
    #   # rec_copy.action_confirm()
    count += 1
#   #   break
record['name'] = '{}-{}'.format(record.name, 1)
record['product_qty'] = 1
record['bom_id'] = bom
# record['procurement_group_id'] = procurement_group_id.id

#   # rec.write({
#   #   'name':'{}-{}'.format(rec.name,1),
#   #   'product_qty':1,
#   #   'bom_id': bom,
#   # 'procurement_group_id' : procurement_group_id.id
#   # })
record._onchange_move_raw()
# # record.action_confirm()

""""
step 2
Confirm ALl backorder and one transfer will be created
"""

procurement_group_id = record.procurement_group_id.id
productions = env['mrp.production'].search([('procurement_group_id', '=', procurement_group_id)])
for mo in productions:
  if mo.state == 'draft':
    mo.action_confirm()


"""
in 2nd server action perform this 3 step (Produce All)

"""

"""
step 1
assign serial for finished goods
"""
for picking in record.picking_ids:
    if picking.state != 'done':
        raise UserError(
            f"Stock picking {picking.name} is not in 'done' state. Please validate the Transfer before proceeding.")

procurement_group_id = record.procurement_group_id.id
productions = env['mrp.production'].search([('procurement_group_id', '=', procurement_group_id)])
for mo in productions:
    if not mo.lot_producing_id:
        mo.action_generate_serial()

"""
step 2 
assign serial no for components to consume
"""

for production in records:
  procurement_group_id = production.procurement_group_id.id
  productions = env['mrp.production'].search([('procurement_group_id', '=', procurement_group_id)])
  for mo in productions:
    if mo.state in ['progress','to_close']:
      for move in mo.move_raw_ids:
        count = 1
        for com in move.move_line_ids:
          com.sudo().write({'qty_done':1})
          if move.should_consume_qty == count:
            break
          count+=1

"""
step 3
validate all back order
"""

procurement_group_id = record.procurement_group_id.id
productions = env['mrp.production'].search([('procurement_group_id', '=', procurement_group_id)])
for mo in productions:
  mo.button_mark_done()


"""
automated action to store vendor serial no from grn(transfer after po) to lot/serial production
"""
# custom field created on lot serial and after po receipt(GRN) - vendor lot/Serial
#model -	Product Moves (Stock Move Line)
#trigger field- custom field (vendor lot/serial)

for rec in record:
  rec.lot_id.update({
    'x_studio_vendor_lotserial':rec.x_studio_vendor_lotserial
  })

"""required field  vendor lot/serial in GRN(transfer receipt)"""
#at product template boolean field will be created for vendor lot serial req or not
#similarly invisible field related to above boolean field new field will be created on GRN(tranfer, receipt)
#condition domain added in vendor lot/serial field with related field

"""one more condition we added to hide produce all button if we click default confirm burron using boolean field"""

#
for record in env['mrp.production'].browse(env.context.get('active_ids', [])):
    bom_id = record.bom_id.id
    count = 2

    try:
        batch_size = 50  # Adjust the batch size according to your server capacity
        total_qty = int(record.product_qty)

        for start in range(1, total_qty, batch_size):
            end = min(start + batch_size, total_qty)
            for r in range(start, end):
                rec_copy = record.copy(default={
                    'name': f'{record.name}-{count}',
                    'product_qty': 1,
                    'procurement_group_id': record.procurement_group_id.id,
                    'bom_id': False,
                    'move_raw_ids': False,
                    'origin': record.origin,
                })
                rec_copy['bom_id'] = bom_id
                rec_copy._onchange_move_raw()
                count += 1

            # Commit the transaction periodically to free up memory
            env.cr.commit()

        # Update the original record
        record.write({
            'name': f'{record.name}-1',
            'product_qty': 1,
            'bom_id': bom_id,
        })
        record._onchange_move_raw()

    except Exception as e:
        raise UserError("An error occurred while creating backorders: %s" % str(e))

for record in env['mrp.production'].browse(env.context.get('active_ids', [])):
    bom_id = record.bom_id.id
    count = 2

    try:
        batch_size = 50  # Adjust the batch size according to your server capacity
        total_qty = int(record.product_qty)

        record.action_confirm()

        # Update the original record
        record.write({
            'state': 'draft',
            'product_qty': 1,
            'bom_id': False,
            'move_raw_ids': False,
        })
        record['bom_id'] = bom_id
        record._onchange_move_raw()
        # moves_raw_values = record._get_moves_raw_values()
        # record.write({'move_raw_ids': [(0, 0, moves_raw_values[0])]})
        # raise UserError(moves_raw_values)

        bom_move_line = record.move_raw_ids.ids

        for start in range(1, total_qty, batch_size):
            end = min(start + batch_size, total_qty)
            for r in range(start, end):
                rec_copy = record.copy(default={
                    'name': f'{record.name}-{count}',
                    'procurement_group_id': record.procurement_group_id.id,
                    'state': 'confirmed',
                    # 'product_qty': 1,
                    'origin': record.origin,
                })
                # rec_copy.write({'state': 'confirmed'})
                # rec_copy.action_confirm()
                count += 1

                # rec_copy.with_context(bypass_reservation_update=True)._onchange_move_raw()
                # k = []
                # for i in moves_raw_values:
                #   s = env['stock.move'].create(i)
                #   k.append(s.id)
                # rec_copy.with_context(bypass_reservation_update=True).write({'bom_id': bom_id,'move_raw_ids': [(6, 0, moves_raw_values[0])]})

            # Commit the transaction periodically to free up memory
            env.cr.commit()

        record.write({
            'name': f'{record.name}-1',
            'state': 'confirmed',
            # 'move_raw_ids': [(6, 0, bom_move_line)],
        })

        # q = []
        # for e in moves_raw_values:
        #   v = env['stock.move'].create(e)
        #   q.append(v.id)
        # record.write({'move_raw_ids': [(6, 0, bom_move_line)]})

    except Exception as e:
        raise UserError("An error occurred while creating backorders: %s" % str(e))

records = env['mrp.production'].browse(env.context.get('active_ids', [])) # Initialize variables
new_records_values = []
bom_id = None
try:
    for record in records:
        bom_id = record.bom_id.id
        count = 2
    for r in range(1, int(record.product_qty)):
        rec_copy_values = { 'name': f'{record.name}-{count}', 'product_qty': 1, 'procurement_group_id': record.procurement_group_id.id, 'bom_id': bom_id, 'move_raw_ids': False, 'origin': record.origin }
        new_records_values.append(rec_copy_values)
        count += 1
    record.write({ 'name': f'{record.name}-1', 'product_qty': 1, 'bom_id': bom_id, })
    record._onchange_move_raw()
    # Create all new records at once
    if new_records_values: env['mrp.production'].create(new_records_values)
except Exception as e:
    raise UserError("An error occurred while creating backorders: %s" % str(e))



#bulk mass mo



# Define your batch size
batch_size = 50

# Gather all records
records = env['mrp.production'].browse(env.context.get('active_ids', []))


# Prepare a list to store new record values
new_records = []

# for record in records:
bom_id = record.bom_id.id
count = 2  # Counter for naming the records
total_qty = int(record.product_qty)

# Update the original record
record.write({
    # 'name': f'{record.name}-1',
    'product_qty': 1,
    'bom_id': bom_id,
})
record._onchange_move_raw()
record.action_confirm()
m_append = []
# for start in range(1, total_qty, batch_size):
    # end = min(start + batch_size, total_qty)
for r in range(1, total_qty):
    new = record.copy({
        'name': f'{record.name}-{count}',
        'product_qty': 1,
        'procurement_group_id': record.procurement_group_id.id,
        'bom_id': bom_id,
        'origin': record.origin,
        'x_studio_analytic_acc_wo':record.x_studio_analytic_acc_wo.id,
    })
    new._onchange_move_raw()
        # new.action_confirm()
    m_append.append(new.id)
    count += 1
# Commit the transaction periodically to free up memory
# env.cr.commit()
record.write({
    'name': f'{record.name}-1',})
# rs=[ac._onchange_move_raw()  for ac in m_append]
# r=[ac.action_confirm()  for ac in m_append]
# Confirm all new records individually
ll = env['mrp.production'].browse(m_append)
ll.action_confirm()
# for new_record in m_append:
#     new_record._onchange_move_raw()
#     new_record.action_confirm()



'''Due to connection timeout the above code is modifed by the following code'''
# create mass backorder in confirm state

# Prepare a list to store new record values
new_records = []

# for record in records:
bom_id = record.bom_id.id
count = 2  # Counter for naming the records
total_qty = int(record.product_qty)

# Update the original record
record.write({
    'product_qty': 1,
    'bom_id': bom_id,
})
record._onchange_move_raw()
record.action_confirm()
m_append = []
for r in range(1, total_qty):
    new = record.copy({
        'name': f'{record.name}-{count}',
        'product_qty': 1,
        'procurement_group_id': record.procurement_group_id.id,
        'bom_id': bom_id,
        'origin': record.origin,
        'x_studio_analytic_acc_wo':record.x_studio_analytic_acc_wo.id,
    })
    new._onchange_move_raw()
    m_append.append(new.id)
    count += 1
record.write({
    'name': f'{record.name}-1',})
# Confirm all new records individually
ll = env['mrp.production'].browse(m_append)
ll.action_confirm()


#produce all
"action assign serial"

if record.picking_ids.state != 'done':
    raise UserError(
        f"Stock picking {picking.name} is not in 'done' state. Please validate the Transfer before proceeding.")


productions = env['mrp.production'].search(
    [('procurement_group_id', '=', record.procurement_group_id.id), ('lot_producing_id', '=', False)])

ls = [mo.action_generate_serial() for mo in productions]



"assign bom component in mo"

# procurement_group_id = record.procurement_group_id.id
productions = env['mrp.production'].search([('procurement_group_id', '=', record.procurement_group_id.id),('state', 'in', ['progress','to_close'])])

for mo in productions.move_raw_ids:
  lst = [com.sudo().write({'qty_done':1}) for com in mo.move_line_ids]



"assign bom components"

productions = env['mrp.production'].search([('procurement_group_id', '=', record.procurement_group_id.id),('state', 'in', ['progress','to_close'])])

for mo in productions.move_raw_ids:
  lst = [com.sudo().write({'qty_done':1}) for com in mo.move_line_ids]



"validate all"

productions = env['mrp.production'].search([('procurement_group_id', '=', record.procurement_group_id.id)])
productions.button_mark_done()








