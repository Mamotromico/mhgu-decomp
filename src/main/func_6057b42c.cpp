// cUIOCustomizedPanel vtable slot +0x1c (MtDTI 6189a320): the cUIObject step, then for modes 3..5 the object at
// +0x5c is called, and the mode is cleared.
struct cUIOCustomizedPanel {
    void *vtable;
    unsigned char ui_object[0x48];
    int mode;
    int *entries;
    unsigned entry_count;
    int field_58;
    void *field_5c;
};

extern "C" void func_6056dc88(void *self);
extern "C" void func_6065b4ac(void *obj);

extern "C" void func_6057b42c(cUIOCustomizedPanel *self)
{
    func_6056dc88(self);
    if ((unsigned)(self->mode - 3) <= 2 && self->field_5c)
        func_6065b4ac(self->field_5c);
    self->mode = 0;
}
