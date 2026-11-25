// cUIOCustomizedPanel deleting destructor (MtDTI 6189a320): as func_6057b0fc, then the object goes back to its
// class allocator.
struct MtAllocator;
typedef void (*MtFreeFn)(MtAllocator *, void *p);

struct MtDTI;

struct cUIOCustomizedPanel {
    void *vtable;
    unsigned char ui_object[0x48];
    int mode;
    int *entries;
    unsigned entry_count;
    int field_58;
    void *field_5c;
};

extern void *D_6176e018[];
extern char D_6191eb18;
extern MtDTI D_6189a320;
extern "C" MtAllocator *func_607aa47c(void *owner);
extern "C" void *func_6056da30(void *self);

static inline void mt_free(MtAllocator *a, void *p)
{
    (*(MtFreeFn *)(*(char **)a + 0x34))(a, p);
}

extern "C" void func_6057b150(cUIOCustomizedPanel *self)
{
    self->vtable = &D_6176e018[2];
    int *entries = self->entries;
    if (entries)
        mt_free(func_607aa47c(&D_6191eb18), entries);
    func_6056da30(self);
    mt_free(func_607aa47c(&D_6189a320), self);
}
