extern "C" int func_61370010(void *p);

namespace nn { namespace os { struct MutexType; int UnlockMutex(MutexType *); } }

extern "C" int func_61370010(void *p) {
    return nn::os::UnlockMutex((nn::os::MutexType *)((char *)p + 0x10));
}