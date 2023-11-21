from hamcrest import assert_that, equal_to


from now_utils.common import Entity, Variable
from now_utils.util import get_connector_name

def test_get_name():
    # GIVEN
    var_name = 'ctrlind_15_OrderBook_Command_Type'
    entity = Entity()
    entity.port_name = var_name
    entity.direction = Variable.Direction.IN

    # WHEN
    con_name = get_connector_name(entity)

    # THEN
    assert_that(con_name, equal_to('in_ip_orderbook_command_type'))
