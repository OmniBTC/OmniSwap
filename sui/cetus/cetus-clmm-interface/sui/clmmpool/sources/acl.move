module cetus_clmm::acl {
    use move_stl::linked_table::LinkedTable;

    struct ACL has store {
        permissions: LinkedTable<address, u128>
    }
}