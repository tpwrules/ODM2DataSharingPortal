/**
 * Created by Mauriel on 1/26/2017.
 */

$(document).ready(function () {
    var snackbarContainer = document.querySelector('#clipboard-snackbar');

    $(".btn-copy").click(function () {
        var data = {
            message: 'Copied to clipboard.',
            timeout: 3000
        };
        snackbarContainer.MaterialSnackbar.showSnackbar(data);
    });

    $(".click-select-all").click(function () {
        $(this).select();
    });

    $(".clipboard-copy").click(function (e) {
        var copyTarget = $(this).attr("data-target");
        copyToClipboard(document.getElementById(copyTarget), e);
    });
});

function copyToClipboard(elem, event) {
    // create hidden text element, if it doesn't already exist
    var targetId = "_hiddenCopyText_";
    var isInput = elem.tagName === "INPUT" || elem.tagName === "TEXTAREA";
    var origSelectionStart, origSelectionEnd;
    if (isInput) {
        // can just use the original source element for the selection and copy
        target = elem;
        origSelectionStart = elem.selectionStart;
        origSelectionEnd = elem.selectionEnd;
    } else {
        // must use a temporary form element for the selection and copy
        target = document.getElementById(targetId);
        if (!target) {
            var target = document.createElement("textarea");
            target.style.position = "absolute";
            target.style.left = "-9999px";
            target.style.top = "0";
            target.id = targetId;
            document.body.appendChild(target);
        }
        target.textContent = elem.textContent;
    }
    // select the content
    var currentFocus = document.activeElement;
    target.focus();
    target.setSelectionRange(0, target.value.length);

    // copy the selection
    var succeed;
    try {
        succeed = document.execCommand("copy");
    } catch (e) {
        succeed = false;
    }
    // restore original focus
    if (currentFocus && typeof currentFocus.focus === "function") {
        currentFocus.focus();
    }

    if (isInput) {
        // restore prior selection
        elem.setSelectionRange(origSelectionStart, origSelectionEnd);
    } else {
        // clear temporary content
        target.textContent = "";
    }

    // Remove temporary input
    if (!isInput) {
        target.remove();
    }

    return succeed;
}