struct func_table {
    void (*f[4])(void *, void *);
};

struct func_table_ref {
    func_table *table;
};

extern "C" void func_60827c84(struct func_table_ref *ref, void *arg)
{
    ref->table->f[3](ref, arg);
}